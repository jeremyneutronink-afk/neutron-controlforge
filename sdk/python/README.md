# Neutron ControlForge Python SDK

Install from the repository root:

```bash
pip install -e sdk/python
```

Example:

```python
from controlforge import ControlForgeClient

with ControlForgeClient(
    base_url="http://127.0.0.1:8000",
    agent_id="YOUR_AGENT_ID",
    api_key="YOUR_AGENT_KEY",
) as guard:
    run = guard.create_run()

    decision = guard.evaluate(
        run_id=run["id"],
        action="read_customer",
        resource="customer/123",
    )

    if decision["decision"] == "ALLOW":
        print(
            guard.execute(
                decision["action_id"]
            )
        )

    guard.complete_run(
        run["id"]
    )
```
