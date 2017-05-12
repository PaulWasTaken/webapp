# webapp
This app lets you to perform some simple stuff with your services like Start, Stop or Reboot it. 
"-p [port]" to specify the port. 8080 by default. 
"-i [ip]" to set preferred ip. 127.0.0.1 by default
If you want to add a custom platform, you should create an executor inherited from AbstracExecutor and add condition to the "choose_executor()" in the WebApp class.