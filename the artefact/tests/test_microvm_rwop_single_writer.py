from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "deployment" / "clayverse-kata-statefulset.template.yaml"
CONTRACT = ROOT / "deployment" / "MICROVM_DEPLOYMENT_CONTRACT.md"


def test_canonical_writable_pvcs_are_single_pod_writer_only():
    text = TEMPLATE.read_text()

    assert text.count('accessModes: ["ReadWriteOncePod"]') == 2
    assert 'accessModes: ["ReadWriteOnce"]' not in text
    assert "STORAGE SINGLE-WRITER LAW" in text
    assert "second pod cannot mount" in text


def test_final_acceptance_requires_rwop_csi_and_negative_competing_pod_probe():
    text = CONTRACT.read_text()

    assert "one-Pod writer fencing" in text
    assert "MUST use Kubernetes `ReadWriteOncePod`, not `ReadWriteOnce`" in text
    assert "CSI storage path that supports RWOP" in text
    assert "second Pod cannot concurrently mount either canonical writable PVC" in text
    assert "competing Pod" in text
    assert "cannot schedule/mount/write" in text
    assert "replacement Pod can acquire the PVC" in text
