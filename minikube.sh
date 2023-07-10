minikube start --driver=docker --alsologtostderr --kubernetes-version=v1.27.0-rc.0 --cpus 8 --memory 13974 --vm-driver=virtualbox

kubectl patch pod elasticsearch --patch '{"spec":{"containers":[{"name":"elasticsearch", "resources":{"requests":{"cpu":"1500m"}, "limits":{"cpu":"1500m"}}}]}}'