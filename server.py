import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 5000
state_tick = 0

class ApiRequestHandler(BaseHTTPRequestHandler):

    def __init__(self, request, client_address, ref_req, api_ref):
        self.api = api_ref
        super().__init__(request, client_address, ref_req)

    def call_api(self, method, path, args):
        if path in api.routing[method]:
            try:
                result = api.routing[method][path](args)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(result, indent=4).encode())
            except Exception as e:
                self.send_response(500, "Server Error")
                self.end_headers()
                self.wfile.write(json.dumps({ "error": e.args }, indent=4).encode())
        else:
            self.send_response(404, "Not Found")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "not found"}, indent=4).encode())

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        args = parse_qs(parsed_url.query)

        for k in args.keys():
            if len(args[k]) == 1:
                args[k] = args[k][0]

        self.call_api("GET", path, args)

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        if self.headers.get("content-type") != "application/json":
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "posted data must be in json format"
            }, indent=4).encode())
        else:
            data_len = int(self.headers.get("content-length"))
            data = self.rfile.read(data_len).decode()
            self.call_api("POST", path, json.loads(data))


class API():
    def __init__(self):
        self.routing = { "GET": { }, "POST": { } }

    def get(self, path):
        def wrapper(fn):
            self.routing["GET"][path] = fn
        return wrapper

    def post(self, path):
        def wrapper(fn):
            self.routing["POST"][path] = fn
        return wrapper

    def __call__(self, request, client_address, ref_request):
        api_handler = ApiRequestHandler(request, client_address, ref_request, api_ref=self)
        return api_handler


api = API()

example_data0 = {
    "items": [
        { "id": 1, "name": "A", "amount": 100, "date":"01-01-2025"},
        { "id": 2, "name": "B", "amount": 0, "date":"01-01-2025"},
        { "id": 3, "name": "C", "amount": 30, "date":"01-01-2025"},
        { "id": 4, "name": "D", "amount": 40, "date":"01-01-2025"},
        { "id": 1, "name": "A", "amount": 30, "date":"03-01-2025"},
        { "id": 2, "name": "B", "amount": 20, "date":"03-01-2025"},
        { "id": 3, "name": "C", "amount": 30, "date":"03-01-2027"},
        { "id": 4, "name": "D", "amount": 40, "date":"03-01-2025"},
        { "id": 1, "name": "A", "amount": 30, "date":"03-01-2025"},
        { "id": 2, "name": "B", "amount": 20, "date":"03-01-2025"},
        { "id": 3, "name": "C", "amount": 30, "date":"03-01-2025"},
        { "id": 4, "name": "D", "amount": 40, "date":"03-01-2026"}
    ]
}
example_data1 = {
    "items": [
        { "id": 1, "name": "A", "amount": 20, "date":"02-01-2025"},
        { "id": 2, "name": "B", "amount": 20, "date":"02-01-2025"},
        { "id": 3, "name": "C", "amount": 30, "date":"02-01-2025"},
        { "id": 4, "name": "D", "amount": 40, "date":"02-01-2025"}
    ]
}
example_data2 = {
    "items": [
        { "id": 1, "name": "A", "amount": 30, "date":"03-01-2025"},
        { "id": 2, "name": "B", "amount": 20, "date":"03-01-2025"},
        { "id": 3, "name": "C", "amount": 30, "date":"03-01-2025"},
        { "id": 4, "name": "D", "amount": 40, "date":"03-01-2025"}
    ]
}

@api.get("/")
def index(_):
    global state_tick
    return_values = [example_data0,example_data1,example_data2]
    return return_values[state_tick] 

@api.get("/tick")
def state_tick_plus_1(_):
    global state_tick
    state_tick = (state_tick + 1) % 3

@api.get("/list")
def list(_):
    return {
        "count": len(example_data["items"]),
        "items": example_data["items"]
    }

@api.get("/search")
def search(args):
    q = args.get("q", None)

    if q is None:
        return { "error": "q parameter required" }
    else:
        results = []
        for item in example_data["items"]:
            if item["name"].count(q) > 0:
                results.append(item)
        return { "count": len(results), "items": results }


@api.post("/add")
def add(args):
    id = example_data["items"].copy().pop()["id"] + 1
    name = args.get("name", None)
    description = args.get("description", None)

    if name is None or description is None:
        return { "error": "name and description are required parameters" }
    else:
        item = { "id": id, "name": name, "description": description }
        example_data["items"].append(item)
        return item


@api.post("/delete")
def delete(args):
    id = args.get("id", None)
    if id is None:
        return { "error": "id parameter required" }
    else:
        item_deleted = False

        for item in example_data["items"]:
            if item["id"] == id:
                example_data["items"].remove(item)
                item_deleted = True
                break

        if item_deleted:
            return { "deleted": id }
        else:
            return { "error": f"item not found with id {id}" }


if __name__ == "__main__":

    httpd = HTTPServer(('', PORT), api)
    print(f"Application started at http://127.0.0.1:{PORT}/")
    httpd.serve_forever()
