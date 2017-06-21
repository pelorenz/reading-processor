import web,sys,os
sys.path.append(os.getcwd())

from server.controller import *
from server.index import *

urls = (
  '/', 'Index',
  '/app/(.+)', 'Controller'
)

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
