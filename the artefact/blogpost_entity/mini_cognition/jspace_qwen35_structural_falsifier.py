import torch
from torch import nn
import functools
from dataclasses import dataclass

# Deterministic regression seed; this is the same bounded structural falsifier.
torch.manual_seed(0)

# Exact structural logic mirrored from anthropics/jacobian-lens
# commit 581d398613e5602a5af361e1c34d3a92ea82ba8e
# for Layout/_find_layout and ActivationRecorder tuple handling.
def _resolve_attr_path(obj, dotted_path):
    return functools.reduce(getattr, dotted_path.split('.'), obj)


@dataclass(frozen=True)
class Layout:
    path: str
    layers: str = 'layers'
    norm: str = 'norm'
    embed: str = 'embed_tokens'
    lm_head: str = 'lm_head'


_LAYOUTS = (
    Layout('model'),
    Layout('model.language_model'),
    Layout('language_model'),
    Layout('model', norm='final_layernorm'),
    Layout('transformer', layers='h', norm='ln_f', embed='wte'),
    Layout('gpt_neox', norm='final_layer_norm', embed='embed_in', lm_head='embed_out'),
)


def _find_layout(hf_model):
    for layout in _LAYOUTS:
        try:
            candidate = _resolve_attr_path(hf_model, layout.path)
        except AttributeError:
            continue
        if all(hasattr(candidate, a) for a in (layout.layers, layout.norm, layout.embed)) and hasattr(hf_model, layout.lm_head):
            return layout
    raise ValueError('layout not found')


class ActivationRecorder:
    def __init__(self, blocks, at, *, start_graph_at=None):
        self._blocks = blocks
        self._indices = sorted(set(at))
        self._start_graph_at = start_graph_at
        if start_graph_at is not None and start_graph_at not in self._indices:
            self._indices = sorted({*self._indices, start_graph_at})
        self.activations = {}
        self._handles = []

    def _make_hook(self, index):
        is_graph_root = index == self._start_graph_at

        def hook(module, inputs, output):
            tensor = output if torch.is_tensor(output) else output[0]
            if is_graph_root:
                tensor.requires_grad_(True)
            self.activations[index] = tensor

        return hook

    def __enter__(self):
        for index in self._indices:
            self._handles.append(self._blocks[index].register_forward_hook(self._make_hook(index)))
        return self

    def __exit__(self, *exc):
        for h in self._handles:
            h.remove()


class HybridBlock(nn.Module):
    def __init__(self, d, *, returns_tuple, kind):
        super().__init__()
        self.proj = nn.Linear(d, d, bias=False)
        nn.init.eye_(self.proj.weight)
        self.returns_tuple = returns_tuple
        self.kind = kind

    def forward(self, x, **kwargs):
        # Slightly different deterministic map per pseudo layer kind.
        y = self.proj(x)
        y = y + (0.03 if self.kind == 'linear_attention' else 0.07) * torch.tanh(y)
        return (y, {'state': self.kind}) if self.returns_tuple else y


class TextConfig:
    num_hidden_layers = 4
    hidden_size = 8


class Config:
    def get_text_config(self):
        return TextConfig()


class FakeTextModel(nn.Module):
    def __init__(self, vocab=32, d=8):
        super().__init__()
        self.embed_tokens = nn.Embedding(vocab, d)
        self.layers = nn.ModuleList([
            HybridBlock(d, returns_tuple=True, kind='linear_attention'),
            HybridBlock(d, returns_tuple=False, kind='linear_attention'),
            HybridBlock(d, returns_tuple=True, kind='linear_attention'),
            HybridBlock(d, returns_tuple=False, kind='full_attention'),
        ])
        self.norm = nn.LayerNorm(d)

    def forward(self, input_ids, use_cache=False):
        x = self.embed_tokens(input_ids)
        for layer in self.layers:
            out = layer(x)
            x = out[0] if isinstance(out, tuple) else out
        return x


class ModelWrapper(nn.Module):
    def __init__(self):
        super().__init__()
        self.language_model = FakeTextModel()


class FakeQwen35ForConditionalGeneration(nn.Module):
    def __init__(self):
        super().__init__()
        self.model = ModelWrapper()
        self.lm_head = nn.Linear(8, 32, bias=False)
        self.config = Config()


m = FakeQwen35ForConditionalGeneration().eval()
for p in m.parameters():
    p.requires_grad_(False)

layout = _find_layout(m)
assert layout.path == 'model.language_model', layout
text = _resolve_attr_path(m, layout.path)
assert len(text.layers) == m.config.get_text_config().num_hidden_layers

ids = torch.tensor([[1, 2, 3, 4, 5]], dtype=torch.long)
with ActivationRecorder(text.layers, at=[0, 3], start_graph_at=0) as rec:
    text(input_ids=ids, use_cache=False)

src = rec.activations[0]
tgt = rec.activations[3]
assert src.requires_grad
assert torch.is_tensor(src) and torch.is_tensor(tgt)

# Jacobian-style gradient: sum one output dimension at all positions.
scalar = tgt[..., 0].sum()
(grad,) = torch.autograd.grad(scalar, src, retain_graph=False, allow_unused=False)
assert grad.shape == src.shape
assert torch.isfinite(grad).all()
assert grad.abs().sum().item() > 0

print('EXPERIMENT=QWEN35_HYBRID_JLENS_STRUCTURAL_FALSIFIER')
print('LAYOUT', layout.path)
print('LAYERS', len(text.layers), 'HIDDEN', m.config.get_text_config().hidden_size)
print('SOURCE_TUPLE_BLOCK_CAPTURED_AS_TENSOR', torch.is_tensor(src))
print('TARGET_CAPTURED_AS_TENSOR', torch.is_tensor(tgt))
print('GRAD_SHAPE', tuple(grad.shape))
print('GRAD_FINITE', bool(torch.isfinite(grad).all()))
print('GRAD_L1', float(grad.abs().sum()))
print('RESULT=MECHANISM_SUPPORTED_NOT_QWEN35_RUNTIME_PROOF')
