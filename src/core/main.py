import uvicorn

if __name__ == "__main__":
    # Run the server
    # host="0.0.0.0" allows access from local network (iPhone)
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
