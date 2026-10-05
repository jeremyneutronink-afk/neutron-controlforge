import os

from controlforge import ControlForgeClient


def require_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"{name} is required."
        )

    return value


def main() -> None:
    base_url = os.getenv(
        "CONTROLFORGE_URL",
        "http://127.0.0.1:8000",
    )

    agent_id = require_env(
        "CONTROLFORGE_AGENT_ID"
    )

    agent_key = require_env(
        "CONTROLFORGE_AGENT_KEY"
    )

    with ControlForgeClient(
        base_url=base_url,
        agent_id=agent_id,
        api_key=agent_key,
    ) as guard:
        print(
            "Health:",
            guard.health(),
        )

        run = guard.create_run()

        print(
            "Created run:",
            run["id"],
        )

        decision = guard.evaluate(
            run_id=run["id"],
            action="issue_refund",
            resource="customer/demo",
            arguments={
                "amount": 100,
            },
            provenance={
                "source": "example_agent",
                "trust": "trusted_internal",
            },
        )

        print(
            "Decision:",
            decision["decision"],
            decision["reason"],
        )

        if decision["decision"] == "ALLOW":
            execution = guard.execute(
                decision["action_id"]
            )

            print(
                "Execution:",
                execution["status"],
            )

        guard.complete_run(
            run["id"]
        )

        print(
            "Run completed."
        )


if __name__ == "__main__":
    main()
