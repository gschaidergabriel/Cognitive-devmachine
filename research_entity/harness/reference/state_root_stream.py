from __future__ import annotations

import hashlib
from typing import Callable


def semantic_state_hash_streaming(*, conn, global_epoch: int, domain_epochs_json: str,
                                  semantic_chain_hash_json: str,
                                  encode_json_scalar: Callable[[object], str]) -> str:
    """Return the legacy StateLedger semantic-state SHA-256 without materializing state.

    Contract: byte-for-byte identical to cjson({
      'global_epoch': ...,
      'domain_epochs': ...,
      'state': ledger.materialized(),
      'semantic_chain_hash': ...,
    }).

    `state.value_json` is written by StateLedger through cjson(), so it is already the exact
    canonical JSON representation required by the legacy hash contract. Reusing those bytes
    avoids JSON decoding, Python object reconstruction and canonical re-encoding for every
    value while preserving the existing root hash exactly.

    This remains O(N) in state rows. It is deliberately NOT a Merkle/root-contract change.
    """
    digest = hashlib.sha256()
    update = digest.update

    def text(value: str) -> None:
        update(value.encode('utf-8'))

    # cjson sorts object keys lexicographically. For the legacy outer root object the exact
    # order is: domain_epochs, global_epoch, semantic_chain_hash, state.
    update(b'{"domain_epochs":')
    text(domain_epochs_json)
    update(b',"global_epoch":')
    text(str(int(global_epoch)))
    update(b',"semantic_chain_hash":')
    text(semantic_chain_hash_json)
    update(b',"state":[')

    first = True
    rows = conn.execute(
        'SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash '
        'FROM state ORDER BY domain,k'
    )
    for row in rows:
        if first:
            first = False
        else:
            update(b',')

        # Exact canonical key order of one materialized state row:
        # domain, domain_epoch, epistemic, key, semantic_hash, status, value.
        update(b'{"domain":')
        text(encode_json_scalar(row[0]))
        update(b',"domain_epoch":')
        text(str(int(row[5])))
        update(b',"epistemic":')
        text(encode_json_scalar(row[3]))
        update(b',"key":')
        text(encode_json_scalar(row[1]))
        update(b',"semantic_hash":')
        text(encode_json_scalar(row[6]))
        update(b',"status":')
        text(encode_json_scalar(row[4]))
        update(b',"value":')
        if row[2] is None:
            update(b'null')
        else:
            # StateLedger is the sole normal writer and stores cjson(value) here.
            # A non-canonical/corrupt row is an integrity defect; this helper must never
            # silently normalize it into a different historical root.
            text(str(row[2]))
        update(b'}')

    update(b']}')
    return digest.hexdigest()
