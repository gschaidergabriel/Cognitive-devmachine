# VPS bridge operating policy

Standing user authorization recorded 2026-08-24:

- Inside `clay-direct-dev`: broad development freedom is authorized. The agent may build, install, download, benchmark, fuzz, ablate, run unusual experiments, test public tools/repos/models, create/delete scratch data, and reconfigure the sandbox as needed for EntityOS/HCU research.
- Storage must be monitored continuously. Before large downloads/builds, check free bytes and expected artifact size. Prefer caches under `/cache`; remove obsolete scratch/build/model artifacts when space pressure rises. Keep a reserve instead of filling the disk.
- The user explicitly authorizes host-side changes that are necessary to create, repair, resize, rebuild, reconfigure, restart, or otherwise administer the `clay-direct-dev` sandbox and its bridge infrastructure.
- Any host-side action outside that sandbox/bridge-administration scope requires fresh explicit user approval before execution. This includes unrelated host files/services, credentials, firewall/routing changes not needed for the sandbox, package changes unrelated to sandbox/bridge administration, destructive host storage changes, reboot/shutdown, and arbitrary host-root shell work.
- Canonical EntityOS/HCU authority/evidence rules remain separate. Experimental success inside the sandbox does not automatically mint canonical runtime/product credit.
- Paid API/service use remains disallowed unless a newer explicit user/canonical authority changes that scope.

This file is an operating boundary for bridge use, not canonical product authority.
