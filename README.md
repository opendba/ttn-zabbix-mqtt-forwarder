Forward all data messages from TheThingsNetwork MQTT to Zabbix as trapper items

# Install 
```bash
$ kubectl create namespace -n ttn
$ kubectl label namespace --overwrite ttn istio-injection=enabled
$ helm upgrade --install ttn-zabbix-mqtt-forwarder  nx/ttn-zabbix-mqtt-forwarder -n ttn
$ kubectl rollout restart deployment ttn-zabbix-mqtt-forwarder-dep -n ttn
```

# Monitor logs
```bash
$ kubectl tail -ns ttn
```

# Scanning with kubesec
```bash
$ kubesec-scan deployment ttn-zabbix-mqtt-forwarder-dep -n ttn
```
