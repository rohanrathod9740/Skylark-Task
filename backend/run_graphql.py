import sys
import json
from backend.monday_client import handle_mock_graphql

def main():
    try:
        # Read GraphQL query from standard input
        input_data = sys.stdin.read()
        if not input_data:
            print(json.dumps({"data": {}}))
            return
            
        payload = json.loads(input_data)
        query = payload.get("query", "")
        
        result = handle_mock_graphql(query)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
