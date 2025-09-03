# Labmarkdown Documentation

## how to run
1. enter the examon folder
2. `docker compose up -d`
3. (optional) `docker compose ps` to check all the container are healthy
4. run `source merge/bin/activate`
5. run `docker exec -it examon-examon-1 bash -c "supervisorctl start plugins:random_pub"`
6. run the programm
    * test_json.py:send random number to kariosdb, timestamp eqaul to realtime.
    * merge.py:merge the job and node chart, output to grafana dashboard as 0/1 value.
    * trans_gragh.py: output the job and node information to dashapp
    * trans_graph_copy: output the job and node information to kariosdb
7. open `http://localhost:3000/`
8. open `Configuration\Data Sources`, search KariosDB
9. edit:URL`http://kairosdb:8083`, Access`Server`
10. Dashboard → Add new panel
11. enter the metric,tags in your code

### some commands
check metricname: curl -s http://localhost:8083/api/v1/metricnames | jq .









### Start the system

<<<<<<< HEAD
1. `wsl -d Ubuntu-22.04`
2. enter the examon folder
3. `docker compose up -d`
4. (optional) `docker compose up` to check all the container are healthy
5. open `http://localhost:3000/`
6. open `Configuration\Data Sources`, search KariosDB
7. edit:URL`http://kairosdb:8083`, Access`Server`
8. Dashboard → Add new panel
9. enter the status,tags in your code
=======
1. `wsl -d Ubuntu-22.04 -u zhanmao`
2. enter the examon folder
3. `docker compose up -d`
4. (optional) `docker compose ps` to check all the container are healthy
5. run `source merge/bin/activate`
6. run `docker exec -it examon-examon-1 bash -c "supervisorctl start plugins:random_pub"`
7. run the programm
    * test_json.py:send random number to kariosdb, timestamp eqaul to realtime.
    * merge.py:merge the job and node chart, output to grafana dashboard as 0/1 value.
    * trans_gragh.py: output the job and node information to dashapp
    * trans_graph_copy: output the job and node information to kariosdb
8. open `http://localhost:3000/`
9. open `Configuration\Data Sources`, search KariosDB
10. edit:URL`http://kairosdb:8083`, Access`Server`
11. Dashboard → Add new panel
12. enter the metric,tags in your code



>>>>>>> master









commands:
create env:python3 -m venv .name
<<<<<<< HEAD
activate: source name/bin/activate
=======
activate: source merge/bin/activate
check random_pub status: sudo supervisorctl status random_pub 
check metricname: curl -s http://localhost:8083/api/v1/metricnames | jq . 
docker exec -it examon-examon-1 bash -c "supervisorctl start plugins:random_pub"

activate plugin: supervisorctl <command> <plugin-name>
>>>>>>> master



