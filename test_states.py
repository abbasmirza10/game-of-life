import pytest
import tileserver as microservice
import middleware
import multiprocessing
import requests
import os
import time


@pytest.fixture(scope="session", autouse=True)
def setup_teardown_each_test():
    mw = multiprocessing.Process(target=lambda: middleware.app.run(port=middleware.MY_PORT))
    ms = multiprocessing.Process(target=lambda: microservice.app.run(port=microservice.MY_PORT))
    mw.start()
    ms.start()
    time.sleep(1)
    yield mw,ms
    mw.terminate()
    ms.terminate()



def test_microservice():
    response = requests.get(microservice.MY_URL+'/ping')
    assert response.status_code == 200
    assert 'state' in response.json()
    assert 'tile' not in response.json()

    assert response.json()['state'] == "Waiting"

    response = requests.post(microservice.MY_URL+'/inform', json={'url': middleware.MY_URL + "/addTS"})
    assert response.status_code == 200
    
    response = requests.get(middleware.MY_URL+'/get_known_servers')
    assert len(response.json()) == 1, "tileserver should respond to middleware's /ping"
    
    response = requests.post(microservice.MY_URL+'/config', json={'width': 10, 'height': 10})
    assert response.status_code == 200

    response = requests.get(microservice.MY_URL+'/change/0/0/0/')
    assert response.status_code == 200

    response = requests.get(microservice.MY_URL+'/change/0/1/0/')
    assert response.status_code == 200

    response = requests.get(microservice.MY_URL+'/change/1/0/1/')
    assert response.status_code == 200

    response = requests.get(microservice.MY_URL+'/change/1/1/2/')
    assert response.status_code == 200

    response = requests.get(microservice.MY_URL+'/ping')
    assert response.status_code == 200
    assert response.json()['state'] == "User Edit"
    assert 'tile' in response.json()
    assert type(response.json()['tile']) is str
    assert len(response.json()['tile']) == 110
    assert response.json()['tile'][0] == '0'
    assert response.json()['tile'][1] == '1'
    assert response.json()['tile'][11] == '0'
    assert response.json()['tile'][12] == '2'

    for i in range(5):
        response = requests.post(microservice.MY_URL+'/tick', data='"'*44)
        assert response.status_code == 200

        response = requests.get(microservice.MY_URL+'/ping')
        assert response.status_code == 200
        assert response.json()['state'] == "Simulating"

    response = requests.get(microservice.MY_URL+'/pause')
    assert response.status_code == 200

    response = requests.get(microservice.MY_URL+'/ping')
    assert response.status_code == 200
    assert response.json()['state'] == "User Edit"

    response = requests.get(microservice.MY_URL+'/stop')
    assert response.status_code == 200

    response = requests.get(microservice.MY_URL+'/ping')
    assert response.status_code == 200
    assert response.json()['state'] == "Waiting"

def test_blinker():
    requests.post(microservice.MY_URL+'/inform', json={'url': middleware.MY_URL + "/addTS"})
    requests.post(microservice.MY_URL+'/config', json={'width': 5, 'height': 5})
    ref1 = '     \n  0  \n  1  \n  2  \n     \n'
    ref2 = '     \n     \n 012 \n     \n     \n'
    for y in range(5):
        row = ref1[y*6:(y+1)*6]
        for x in range(5):
            response = requests.get(microservice.MY_URL+f'/change/{x}/{y}/{row[x]}/')
    tile = requests.get(microservice.MY_URL+'/ping').json()['tile']
    assert len(tile) == len(ref1)
    for i in range(len(ref1)):
        assert (tile[i] == ' ') == (ref1[i] == ' ')
        assert (tile[i] == '\n') == (ref1[i] == '\n')
    tile = requests.post(microservice.MY_URL+'/tick', data='"'*24).text
    assert len(tile) == len(ref2)
    for i in range(len(ref2)):
        assert (tile[i] == ' ') == (ref2[i] == ' ')
        assert (tile[i] == '\n') == (ref2[i] == '\n')
    tile = requests.post(microservice.MY_URL+'/tick', data='"'*24).text
    assert len(tile) == len(ref1)
    for i in range(len(ref1)):
        assert (tile[i] == ' ') == (ref1[i] == ' ')
        assert (tile[i] == '\n') == (ref1[i] == '\n')
