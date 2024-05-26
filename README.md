### How to run?

#### First clone our repository (make sure that the branch you clone is app)

#### Run in your terminal (ensure that docker desktop is running): 
```bash
docker build -t my_flask_app .
```
#### After the first command is ran, run this next:
```bash
docker run -p 5001:5000 my_flask_app
```
#### The app is now available here:
```bash
http://localhost:5001/
```
