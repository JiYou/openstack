json = """[
    {
        "OS-EXT-STS:vm_state": "active",
        "OS-EXT-SRV-ATTR:instance_name": "instance-00000001",
        "flavor": {
            "name": "m1.tiny",
            "ram": 512,
            "vcpus": 1,
            "swap": "",
            "rxtx_factor": 1,
            "OS-FLV-EXT-DATA:ephemeral": 0,
            "disk": 0,
            "id": "1"
        },
        "user": {
            "id": "4e396e83369f4aab81a08bf93b5cb7b3",
            "name": "admin",
            "email": "admin@example.com"
        },
        "tenant": {
            "id": "cd82e5ce8e274f568b7b949e3cf6b350",
            "name": "demo"
        },
        "OS-EXT-STS:task_state": null,
        "image": {
            "id": "fd9bbb0a-2ebf-405f-8773-55574751388a"
        },
        "id": "242c671a-a9f8-4a38-90b6-f196649f520d",
        "user_id": "4e396e83369f4aab81a08bf93b5cb7b3",
        "status": "ACTIVE",
        "updated": "2012-03-22T20:59:38Z",
        "hostId": "0165abf99d3e318b26eef9e0465671c6e13e40ae13d3bfe2625105cf",
        "OS-EXT-SRV-ATTR:host": "ubuntu",
        "name": "instanceOne",
        "created": 1332478770,
        "tenant_id": "cd82e5ce8e274f568b7b949e3cf6b350"
    },
    {
        "OS-EXT-STS:vm_state": "active",
        "OS-EXT-SRV-ATTR:instance_name": "instance-00000001",
        "flavor": {
            "name": "m2.small",
            "ram": 1024,
            "vcpus": 2,
            "swap": "",
            "rxtx_factor": 1,
            "OS-FLV-EXT-DATA:ephemeral": 0,
            "disk": 0,
            "id": "2"
        },
        "user": {
            "id": "4e396e8g369f4aab81a08bf93b5cb7b3",
            "name": "demo"
        },
        "tenant": {
            "id": "cd82e5ce8e274f568b7b949e3cf6b350",
            "name": "demo"
        },
        "OS-EXT-STS:task_state": null,
        "image": {
            "id": "fd9bbb0a-2ebf-405f-8773-55574751388a"
        },
        "id": "242c671a-a9f8-4a38-90b6-f196649f520d",
        "user_id": "4e396e83369f4aab81a08bf93b5cb7b3",
        "status": "ACTIVE",
        "updated": "2012-03-22T20:59:38Z",
        "hostId": "0165abf99d3e318b26eef9e0465671c6e13e40ae13d3bfe2625105cf",
        "OS-EXT-SRV-ATTR:host": "other",
        "name": "instanceOne",
        "created": 1332478770,
        "tenant_id": "cd82e5ce8e274f568b7b949e3cf6b350"
    },
    {
        "OS-EXT-STS:vm_state": "active",
        "OS-EXT-SRV-ATTR:instance_name": "instance-00000001",
        "flavor": {
            "name": "m1.tiny",
            "ram": 512,
            "vcpus": 1,
            "swap": "",
            "rxtx_factor": 1,
            "OS-FLV-EXT-DATA:ephemeral": 0,
            "disk": 0,
            "id": "1"
        },
        "user": {
            "id": "4e396e8336gf4aab81a08bf93b5cb7b3",
            "name": "demo",
            "email": "admin@example.com"
        },
        "tenant": {
            "id": "dd82e5ce8e274f568b7b949e3cf6b350",
            "name": "other"
        },
        "OS-EXT-STS:task_state": null,
        "image": {
            "id": "fd9bbb0a-2ebf-405f-8773-55574751388a"
        },
        "id": "242c671a-a9f8-4a38-90b6-f196649f520d",
        "user_id": "4e396e83369f4aab81a08bf93b5cb7b3",
        "status": "ACTIVE",
        "updated": "2012-03-22T20:59:38Z",
        "hostId": "0165abf99d3e318b26eef9e0465671c6e13e40ae13d3bfe2625105cf",
        "OS-EXT-SRV-ATTR:host": "ubuntu",
        "name": "instanceOne",
        "created": 1332478770,
        "tenant_id": "cd82e5ce8e274f568b7b949e3cf6b350"
    },
    {
        "OS-EXT-STS:vm_state": "active",
        "OS-EXT-SRV-ATTR:instance_name": "instance-00000001",
        "flavor": {
            "name": "m2.small",
            "ram": 1024,
            "vcpus": 2,
            "swap": "",
            "rxtx_factor": 1,
            "OS-FLV-EXT-DATA:ephemeral": 0,
            "disk": 0,
            "id": "2"
        },
        "user": {
            "id": "4e396e83369f4aab81a08bf93b5cb7b3",
            "name": "admin",
            "email": "admin@example.com"
        },
        "tenant": {
            "id": "cd82e5ce8e274f568b7b949e3cf6b350",
            "name": "demo"
        },
        "OS-EXT-STS:task_state": null,
        "image": {
            "id": "fd9bbb0a-2ebf-405f-8773-55574751388a"
        },
        "id": "242c671a-a9f8-4a38-90b6-f196649f520d",
        "user_id": "4e396e83369f4aab81a08bf93b5cb7b3",
        "status": "ACTIVE",
        "updated": "2012-03-22T20:59:38Z",
        "hostId": "0165abf99d3e318b26eef9e0465671c6e13e40ae13d3bfe2625105cf",
        "OS-EXT-SRV-ATTR:host": "ubuntu",
        "name": "instanceOne",
        "created": 1332478770,
        "tenant_id": "cd82e5ce8e274f568b7b949e3cf6b350"
    },
    {
        "OS-EXT-STS:vm_state": "active",
        "OS-EXT-SRV-ATTR:instance_name": "instance-00000001",
        "flavor": {
            "name": "m1.tiny",
            "ram": 512,
            "vcpus": 1,
            "swap": "",
            "rxtx_factor": 1,
            "OS-FLV-EXT-DATA:ephemeral": 0,
            "disk": 0,
            "id": "1"
        },
        "user": {
            "id": "4e396e83369f4aab81a08bf93b5cb7b3",
            "name": "admin",
            "email": "admin@example.com"
        },
        "tenant": {
            "id": "dd82e5ce8e274f568b7b949e3cf6b350",
            "name": "other"
        },
        "OS-EXT-STS:task_state": null,
        "image": {
            "id": "fd9bbb0a-2ebf-405f-8773-55574751388a"
        },
        "id": "242c671a-a9f8-4a38-90b6-f196649f520d",
        "user_id": "4e396e83369f4aab81a08bf93b5cb7b3",
        "status": "ACTIVE",
        "updated": "2012-03-22T20:59:38Z",
        "hostId": "0165abf99d3e318b26eef9e0465671c6e13e40ae13d3bfe2625105cf",
        "OS-EXT-SRV-ATTR:host": "ubuntu",
        "name": "instanceOne",
        "created": 1332478770,
        "tenant_id": "cd82e5ce8e274f568b7b949e3cf6b350"
    },
    {
        "OS-EXT-STS:vm_state": "active",
        "OS-EXT-SRV-ATTR:instance_name": "instance-00000001",
        "flavor": {
            "name": "m3.medium",
            "ram": 1024,
            "vcpus": 4,
            "swap": "",
            "rxtx_factor": 1,
            "OS-FLV-EXT-DATA:ephemeral": 0,
            "disk": 0,
            "id": "1"
        },
        "user": {
            "id": "4e396e83369f4aab81a08bf93b5cb7b3",
            "name": "admin",
            "email": "admin@example.com"
        },
        "tenant": {
            "id": "dd82e5ce8e274f568b7b949e3cf6b350",
            "name": "other"
        },
        "OS-EXT-STS:task_state": null,
        "image": {
            "id": "fd9bbb0a-2ebf-405f-8773-55574751388a"
        },
        "id": "242c671a-a9f8-4a38-90b6-f196649f520d",
        "user_id": "4e396e83369f4aab81a08bf93b5cb7b3",
        "status": "ACTIVE",
        "updated": "2012-03-22T20:59:38Z",
        "hostId": "0165abf99d3e318b26eef9e0465671c6e13e40ae13d3bfe2625105cf",
        "OS-EXT-SRV-ATTR:host": "other",
        "name": "instanceOne",
        "created": 1332478770,
        "tenant_id": "cd82e5ce8e274f568b7b949e3cf6b350"
    }
]
"""
