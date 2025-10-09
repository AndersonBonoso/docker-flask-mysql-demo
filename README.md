\# Docker + Flask + MySQL (2 containers)



Demo com \*\*Flask\*\* (API) e \*\*MySQL 5.7\*\* orquestrados por \*\*Docker Compose\*\*.



\## Como rodar

```bash

docker compose up -d --build

curl http://localhost:5050/health

curl -X POST http://localhost:5050/users -H "Content-Type: application/json" -d '{ "name":"Anderson","username":"Ander","password":"123@Teste" }'

curl http://localhost:5050/users



