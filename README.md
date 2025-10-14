# Docker + Flask + MySQL (2 containers)

Demo com **Flask** (API) e **MySQL 5.7** orquestrados por **Docker Compose**.

Links e notas do projeto podem ser adicionados aqui.

## Como rodar (Docker)

1. Construa e suba os containers:

```bash
docker compose up -d --build
```

2. Verifique o health da API:

```bash
curl http://localhost:5050/health
```

3. Teste criação/listagem de usuários:

```bash
curl -X POST http://localhost:5050/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Anderson","username":"ander","password":"123@Teste"}'

curl http://localhost:5050/users
```

## Como rodar localmente (sem Docker)

1. Crie e ative um virtualenv com Python 3.11+

```powershell
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r web/requirements.txt
```

2. Exporte variáveis de ambiente (opcional) e execute:

```powershell
setx DB_HOST "localhost"
setx DB_PORT "3306"
setx DB_NAME "teste"
setx DB_USER "app"
setx DB_PASSWORD "app123"
python web/app.py
```

Observação: sem um banco MySQL acessível a aplicação retornará 503 no endpoint `/health`.

## Troubleshooting

- Se o container do MySQL demorar a inicializar, o `docker compose up` pode mostrar erros no web service até o DB estar pronto. Confira os logs com `docker compose logs -f db`.
- Se receber `No module named 'flask'` ao rodar localmente, instale as dependências com `pip install -r web/requirements.txt`.
- As credenciais padrão estão em `docker-compose.yml` (usuário `app`, senha `app123`, DB `teste`).
\# Docker + Flask + MySQL (2 containers)

[COLE AQUI O LINK] do vídeo (quando gravar).

Link do board:

https://github.com/users/AndersonBonoso/projects/1

Demo com \*\*Flask\*\* (API) e \*\*MySQL 5.7\*\* orquestrados por \*\*Docker Compose\*\*.



\## Como rodar

```bash

docker compose up -d --build

curl http://localhost:5050/health

curl -X POST http://localhost:5050/users -H "Content-Type: application/json" -d '{ "name":"Anderson","username":"Ander","password":"123@Teste" }'

curl http://localhost:5050/users



