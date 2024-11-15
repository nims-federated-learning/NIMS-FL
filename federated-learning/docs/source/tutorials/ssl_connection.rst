

Using SSL (secure) connection
==============================================


In order to have secure connection we are using SSL certificate to make the connection
between client and server. Here we will detail the step to create those certificates.

On the server system
"""""""""""""""""""""""

We first need to create the root private key and a self-signed root certificate.

We `generate an RSA private key <https://www.openssl.org/docs/manmaster/man1/openssl-genrsa.html>`_
with des3 encryption method with the name ``rootCA.key`` with a size of 2048 bits.

.. code:: none

    openssl genrsa -des3 -out rootCA.key 2048


We then `generate a certificate requests (CSRs) certificate <https://www.openssl.org/docs/manmaster/man1/openssl-req.html>`_
name ``rootCA.pem`` based on the rootCA.key generated valid for 1024 days.

.. code:: none

    openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 1024 -out rootCA.pem



Next, we create a server private key, a server certificate signing request (CSR),
and we sign the CSR using the root certificate.

We generate server key:

.. code:: none

    openssl genrsa -out server.key 2048


Generate a server certificate signing request (CSR):

.. code:: none

    openssl req -new -key server.key -out server.csr


.. note::

    Here you must indicate `Common Name` that will be use to connect to this server
    This name will be use in the client configuration, the default value is :

    ``"options": "[[grpc.ssl_target_name_override", "localhost"]]``

    Output example

    .. code:: none

        Country Name (2 letter code) [AU]:.
        State or Province Name (full name) [Some-State]:.
        Locality Name (eg, city) []:.
        Organization Name (eg, company) [Internet Widgits Pty Ltd]:.
        Organizational Unit Name (eg, section) []:.
        Common Name (e.g. server FQDN or YOUR name) []:myserver (use localhost for default)
        Email Address []:


Finally `sign the certificate <https://www.openssl.org/docs/manmaster/man1/openssl-x509.html>`_
using the rootCA.pem and rootCA.key previously generated.

.. code:: none

    openssl x509 -req -in server.csr -CA rootCA.pem -CAkey rootCA.key -CAcreateserial -out server.crt -days 500 -sha256


On the client system
"""""""""""""""""""""

The client creates a private key and a certificate signing request (CSR).

.. code:: none

    openssl genrsa -out client.key 2048
    openssl req -new -key client.key -out client.csr

.. note::

    The client will need to enter a Common Name which needs to be the same has
    the one in the above generated CSR.



Client send its CSR to the server which signs it and send it back along with `rootCA.pem` to the client.
So on the server system the following command needs to be run.

.. code:: none

    openssl x509 -req -in client.csr -CA rootCA.pem -CAkey rootCA.key -CAcreateserial -out client.crt -days 500 -sha256


Configuration set up:
""""""""""""""""""""""


Then we can launch a training by modifying the following parameters:

- **Server side**:

.. code:: javascript

    {
        "use_secure_connection": True,
        "ssl_private_key": "server.key",
        "ssl_cert": "server.crt",
        "ssl_root_cert": "rootCA.pem"
    }

``use_secure_connection (default=false)``

When true, the communication will be performed through HTTPS protocol. The 3 SSL files specified below must be valid for this to work.

``ssl_private_key (default="data/certificates/server.key")``

gRPC secure communication private key

``ssl_cert (default="data/certificates/server.crt")``

gRPC secure communication SSL certificate

``ssl_root_cert (default="data/certificates/rootCA.pem")``

gRPC secure communication trusted root certificate


- **Client side**:

.. code:: javascript

    {
        "use_secure_connection": True,
        "ssl_private_key": "client.key",
        "ssl_cert": "client.crt",
        "ssl_root_cert": "rootCA.pem"
    }

``use_secure_connection (default=false)``

When true, the communication will be performed through HTTPS protocol. The 3 SSL files specified below must be valid for this to work.

``ssl_private_key (default="data/certificates/client.key")``

gRPC secure communication private key

``ssl_cert (default="data/certificates/client.crt")``

gRPC secure communication SSL certificate

``ssl_root_cert (default="data/certificates/rootCA.pem")``

gRPC secure communication trusted root certificate