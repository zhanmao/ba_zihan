# Labmarkdown Documentation

## Set up and Installation

### Installing docker and examon on Linux vm
- **OS** Ubuntu-22.04(Virtual Machine)
- **Software Install:**
    -Docker
    -Examon tools
    -

#### Steps Taken:
1. Updated system packages.
2. Installed necessary dependencies.
3. git clone `https://github.com/ExamonHPC/examon.git`
4. edit grafana version in docker-compose.yml: image:grafana/grafana:9.5.15 -for node graph in dashboard
5. reinstall kariosdb connection in new grafana: docker exec -it examon-grafana-1 /bin/bash
                                                 grafana-cli plugins install grafana-kairosdb-datasource

   


### Start the system

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












commands:
create env:python3 -m venv .name
activate: source merge/bin/activate
check random_pub status: sudo supervisorctl status random_pub 
check metricname: curl -s http://localhost:8083/api/v1/metricnames | jq . 
docker exec -it examon-examon-1 bash -c "supervisorctl start plugins:random_pub"
activate plugin: supervisorctl <command> <plugin-name>