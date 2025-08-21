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
<<<<<<< HEAD
4. edit:
    - `docker-compose.yml` :
        kairosdb:
        build:
          context: ./docker/kairosdb
        image: examonhpc/kairosdb:1.2.2

    -  `Dockerfile` in the master folder :
        DELETE:
            Create a backup of the existing sources.list
            RUN mv /etc/apt/sources.list /etc/apt/sources.list.backup

            Create a new sources.list file
            RUN touch /etc/apt/sources.list

            Debian strech moved to archived
            RUN echo "deb https://debian.mirror.garr.it/debian-archive/ stretch main"   > /   etc/  apt/sources.list
        
        EDIT:
            RUN apt-get update && apt-get install -y \
            apt-transport-https \
            ca-certificates \
            libffi-dev \
            build-essential \
            libssl-dev \
            python3-dev \
	        && rm -rf /var/lib/apt/lists/*
    
    - \docker\kairosdb\ `Dockerfile`
        EDIT:
            RUN set -eux ; \
	        sed -i 's|https://ubuntu.mirror.garr.it/ubuntu|http://archive.ubuntu.com/       ubuntu|g' /etc/apt/sources.list; \
	        apt-get update; \
	        apt-get install -y --no-install-recommends \
	        wget \
	        ca-certificates; \
	        rm -rf /var/lib/apt/lists/*
    - \publishers\random_pub\ `random_pub.conf`
=======
4. edit grafana version in docker-compose.yml: image:grafana/grafana:9.5.15 -for node graph in dashboard
5. reinstall kariosdb connection in new grafana: docker exec -it examon-grafana-1 /bin/bash
                                                 grafana-cli plugins install grafana-kairosdb-datasource

   
>>>>>>> master


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
