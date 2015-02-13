# Portrait Domain

This is a project demo developed for the [OpenGLAM.ch Hackathon](http://openglam.ch) in Berne, Switzerland on February 27-28, 2015. For background information see the [concept](https://docs.google.com/document/d/1qBTeD2aGTcyGEKOV28KBpriDiGb5BBiKpRs48SAEB3w/edit?usp=sharing).

####Stack

| Tool   |      Name      |  Advantage |
|----------|:-------------:|------|
| Server distro |  Ubuntu 14.10 x64 | Latest linux |
| WSGI proxy |    Gunicorn   |   Manage workers automatically |
| Web proxy | Nginx |    Fast and easy to configure|
| Framework | Flask |Single file approach for MVC |
| Data store | MongoDB | No scheme needed and scalable|
| DevOps | Fabric | Agentless and Pythonic  |

In addition, a [Supervisor](http://supervisord.org/) running on the server provides a daemon to protect the Gunicorn-Flask process. 

####The MiniTwit app
Based on the [MiniTwit application](https://github.com/mitsuhiko/flask/tree/master/examples/minitwit), which is a prototype of Twitter like multiple-user social network. The original application depends on SQLite. However, the data store could be modified to fit the category of NoSQL such as Google Data Store or MongoDB.

####Deployment

#####1. Install Fabric and clone the Github repo
The DevOps tool is [fabric](https://github.com/fabric/fabric) that is simply based on SSH. The `fabfile.py` and the staging `flask` files are stored on Github. We should install `fabric` and download the fabfile.py on the local machine before the deployment.
```bash
sudo pip install fabric 
wget https://raw.githubusercontent.com/dapangmao/minitwit-mongo-ubuntu/master/fabfile.py
fab -l
```

#####2. Input IP from the virtual machine
A new VM usually emails IP address and the root password. Then we could modify the head part of the `fabfile.py` accordingly. There are quite a few cheaper cloud provider for prototyping other than Amazon EC2. For example, a minimal instance from DigitalOcean only costs five dollars a month. If SSH key has been uploaded, the password could be ignored. 

```python
env.hosts = ['YOUR IP ADDRESS'] # <--------- Enter the IP address
env.user = 'root'
env.password = 'YOUR PASSWORD'  # <--------- Enter the root password
```

#####3. Fire up Fabric
Now it is time to formally deploy the application. With the command below, the `fabric` will first install `pip, git, nginx, gunicorn, supervisor` and the latest `MongodB`, and configure them sequentially.  In less than 5 minutes, a Flask and MongoDB application will be ready for use. Since DigitalOcean has its own software repository for Ubuntu, and its VMs are on SSD, the deployment is even faster, which is usually finished in one minute.   
```python
fab deploy_minitwit
```


