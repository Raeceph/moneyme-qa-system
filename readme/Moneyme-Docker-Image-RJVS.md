
# MONEYME AI Q&A System - Docker Image

## Here is my Docker Image Link:

https://hub.docker.com/r/rjisamood2020/moneyme-qa

This link will allow to view and pull your image from Docker Hub.

---

## Pull and Run the Image (for others):
To run your **MONEYME AI Q&A System** on another machine, use the following command to pull the image:

```bash
docker pull rjisamood2020/moneyme-qa:latest
```

Then, you can run the application with the following command:

```bash
docker run -d -p 8000:8000 rjisamood2020/moneyme-qa:latest
```

This will start the **FastAPI** server, making the application available at [http://localhost:8000](http://localhost:8000).

---

## Testing the Setup:
You can test the system by uploading a PDF or making queries either via the **API** or **CLI**.
