import sys
import os
import json

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agent_resolver import ask_agent

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No query provided"}))
        return
        
    query = sys.argv[1]
    try:
        response, sql = ask_agent(query)
        print(json.dumps({
            "response": response,
            "sql": sql
        }))
    except Exception as e:
        print(json.dumps({
            "error": str(e)
        }))

if __name__ == "__main__":
    main()
