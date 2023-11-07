# JNCEP Web Service

This Flask-based application opens the JNCEP utility up to simple HTTP requests. It can easily be spun up using Docker Compose.

## Credits

This project builds upon the work of JNCEP created by [gvellut](https://github.com/gvellut). The original repository can be found at [gvellut/jncep](https://github.com/gvellut/jncep). I'm thankful to gvellut since i've been using his code for maybe close to a year now. And i've only recent gotten around to swapping my own personal over to this system. This interface is also completely unaffiliated with J-Novel Club and is just a personal and or community project.


## Quickstart

To get started, ensure you have Docker and Docker Compose installed on your system, then follow these steps:

1. Clone the repository:

```bash
git clone https://github.com/itslightmind/jncep-web-service.git
```

2. Navigate to the project directory:

```bash
cd jncep-web-service
```

3. Build and run the container:

```bash
docker-compose up --build
```

The service will be available by default at `http://localhost:5000`.

### Generate an EPUB

```bash
curl -X POST http://localhost:5000/generate-epub \
     -H "Content-Type: application/json" \
     -d '{"jnovel_club_url": "https://j-novel.club/series/ascendance-of-a-bookworm#volume-1"}'
```

### Generate an EPUB with Specific Parts

```bash
curl -X POST http://localhost:5000/generate-epub \
     -H "Content-Type: application/json" \
     -d '{"jnovel_club_url": "https://j-novel.club/series/ascendance-of-a-bookworm#volume-1", "parts": "1-3"}'
```

### Download latest volumes/parts

```bash
curl http://localhost:5000/sync
```

### List Tracked Items

```bash
curl http://localhost:5000/list
```

### Update tracked series

```bash
curl http://localhost:5000/track
```

### Visit to download the epubs

```bash
http://localhost:5000/
```
