"""CLI Entry Point for Brand Guardian AI (Google Cloud version)."""
import uuid
import json
import logging

from dotenv import load_dotenv
load_dotenv(override=True)

from backend.src.graph.workflow import app

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("brand-guardian-runner")


def run_cli_simulation():
    session_id = str(uuid.uuid4())
    logger.info(f"Starting Audit Session: {session_id}")

    initial_inputs = {
        "video_url": "https://youtu.be/dT7S75eYhcQ",
        "video_id": f"vid_{session_id[:8]}",
        "compliance_results": [],
        "errors": [],
        "retry_count": 0,          # NEW: for retry logic
        "indexer_success": False,   # NEW: for conditional routing
    }

    print(f"\n--- Input Payload ---")
    print(json.dumps(initial_inputs, indent=2))

    try:
        final_state = app.invoke(initial_inputs)
        print("\n=== COMPLIANCE AUDIT REPORT ===")
        print(f"Video ID:  {final_state.get('video_id')}")
        print(f"Status:    {final_state.get('final_status')}")

        results = final_state.get('compliance_results', [])
        if results:
            print("\n[ VIOLATIONS ]")
            for issue in results:
                print(f"  - [{issue.get('severity')}] {issue.get('category')}: {issue.get('description')}")
        else:
            print("\n  No violations found. ✅")

        print(f"\n[ REPORT ]\n{final_state.get('final_report')}")

    except Exception as e:
        logger.error(f"Workflow Failed: {str(e)}")
        raise


if __name__ == "__main__":
    run_cli_simulation()
