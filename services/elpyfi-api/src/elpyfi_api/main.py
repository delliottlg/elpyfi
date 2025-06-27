import uvicorn
from .server import app


if __name__ == "__main__":
    uvicorn.run("src.elpyfi_api.main:app", host="0.0.0.0", port=9002, reload=True)



# PM Claude test - agent dispatch working!
# Comment 1: Testing agent dispatch
# Comment 2: Agent still working
# Comment 3: Task completed!
