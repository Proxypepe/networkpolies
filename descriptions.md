```
clusterwide-deny-all.yaml

apiVersion: cilium.io/v2
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: deny-all
spec:
  endpointSelector: {}
  ingress:
  - {}
  egress:
  - {}
```

Файл clusterwide-deny-all.yaml определяет CiliumClusterwideNetworkPolicy — политику безопасности на уровне всего кластера Kubernetes, которая запрещает весь входящий (ingress) и исходящий (egress) трафик для всех подов (pods), если явно не разрешено другими политиками.

Разбор политики:
yaml
apiVersion: cilium.io/v2
kind: CiliumClusterwideNetworkPolicy  # Применяется ко всему кластеру (а не только к namespace)
metadata:
  name: deny-all  # Название политики
spec:
  endpointSelector: {}  # Применяется ко всем Pod'ам (пустой селектор = все endpoints)
  ingress:
  - {}  # Блокирует весь входящий трафик (любые источники и порты)
  egress:
  - {}  # Блокирует весь исходящий трафик (любые назначения и порты)
Что делает эта политика?
Запрещает весь ingress-трафик (входящие соединения к подам).

Никакие внешние сервисы или другие поды не смогут подключиться к подам, если не будут явно разрешены другими политиками.

Запрещает весь egress-трафик (исходящие соединения из подов).

Поды не смогут обращаться к API Kubernetes, DNS, другим сервисам или интернету, пока не будут добавлены разрешающие правила.

Зачем это нужно?
Это базовая политика безопасности, которая реализует принцип "deny by default".

После её применения нужно добавлять более конкретные политики (CiliumNetworkPolicy или CiliumClusterwideNetworkPolicy), чтобы разрешить необходимый трафик.

Пример использования:
Применяем политику:

bash
kubectl apply -f clusterwide-deny-all.yaml
После этого:

Все сетевые соединения блокируются.

Нужно добавить разрешающие правила для критически важного трафика (например, DNS, API Kubernetes, межсервисное взаимодействие).

Как разрешить трафик поверх этой политики?
Нужно создать дополнительные политики с более узкими правилами, например:

yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-dns
  namespace: default
spec:
  endpointSelector: {}  # Применяется ко всем подам в namespace `default`
  egress:
  - toEndpoints:
    - matchLabels:
        k8s:io.kubernetes.pod.namespace: kube-system
        k8s-app: kube-dns
    toPorts:
    - ports:
      - port: "53"
        protocol: UDP
Эта политика разрешит подам в default namespace обращаться к DNS (CoreDNS) в kube-system.

Вывод:
clusterwide-deny-all.yaml — это строгая политика "запретить всё", которая обеспечивает безопасность по умолчанию, но требует дальнейшей настройки разрешений.


```
allow-all-pods-to-coredns.yaml
apiVersion: cilium.io/v2
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: allow-all-pods-to-coredns
spec:
  endpointSelector: {}
  egress:
    - toEndpoints:
        - matchLabels:
            k8s-app: kube-dns
            io.kubernetes.pod.namespace: kube-system
      toPorts:
        - ports:
            - port: "53"
              protocol: UDP
            - port: "53"
              protocol: TCP
```

allow-all-pods-to-coredns.yaml
Эта политика разрешает всем подам (Pods) в кластере Kubernetes обращаться к CoreDNS (системному DNS-серверу) на стандартных портах 53/TCP и 53/UDP.

Структура политики
yaml
apiVersion: cilium.io/v2
kind: CiliumClusterwideNetworkPolicy  # Действует на весь кластер (не ограничено namespace)
metadata:
  name: allow-all-pods-to-coredns  # Название политики
spec:
  endpointSelector: {}  # Применяется ко всем Pod'ам (пустой селектор = все endpoints)
  egress:  # Правила для исходящего трафика (из Pod'ов)
    - toEndpoints:  # Куда разрешён трафик?
        - matchLabels:  # Выбираем Pod'ы CoreDNS по их меткам
            k8s-app: kube-dns  # Метка, указывающая на CoreDNS
            io.kubernetes.pod.namespace: kube-system  # CoreDNS работает в kube-system
      toPorts:  # Какие порты разрешены?
        - ports:
            - port: "53"  # DNS-порт (UDP — основной)
              protocol: UDP
            - port: "53"  # DNS-порт (TCP — используется для больших ответов)
              protocol: TCP
Что делает эта политика?
Разрешает всем подам (endpointSelector: {}) обращаться к CoreDNS.

Без этой политики (если включена deny-all) Pod'ы не смогут резолвить доменные имена.

Разрешает только DNS-трафик (порт 53) на Pod'ы с метками k8s-app: kube-dns в kube-system.

Это стандартные метки CoreDNS в Kubernetes.

Разрешает как UDP (основной протокол DNS), так и TCP (используется для больших запросов).

Зачем это нужно?
Без DNS Pod'ы не смогут:

Разрешать имена сервисов (service.namespace.svc.cluster.local).

Обращаться к внешним доменам (если CoreDNS настроен на форвардинг запросов).

Эта политика дополняет deny-all, позволяя критически важному DNS-трафику работать.

Пример использования
Применяем политику:

bash
kubectl apply -f allow-all-pods-to-coredns.yaml
Результат:

Все Pod'ы теперь могут резолвить DNS-имена.

Остальной трафик (кроме DNS) по-прежнему блокируется (deny-all).

Как проверить, что политика работает?
Запустим тестовый Pod:

bash
kubectl run -it --rm --image=alpine test-pod -- sh
Проверим DNS:

bash
nslookup kubernetes.default.svc.cluster.local
Если разрешение работает → политика применена корректно.

Если нет → проверьте метки CoreDNS:

bash
kubectl get pods -n kube-system -l k8s-app=kube-dns --show-labels
Как можно доработать политику?
Если нужна более строгая настройка, можно:

Ограничить разрешение DNS только определённым namespace:

yaml
endpointSelector:
  matchLabels:
    io.kubernetes.pod.namespace: my-namespace  # Только Pod'ы в my-namespace
Разрешить DNS только для конкретных Pod'ов:

yaml
endpointSelector:
  matchLabels:
    app: my-app  # Только Pod'ы с меткой app=my-app
Вывод
Политика allow-all-pods-to-coredns.yaml критически важна для работы кластера, так как:
✅ Разрешает DNS-запросы, без которых многие сервисы не работают.
✅ Гибко настраивается под требования безопасности.
🚀 Рекомендуется применять вместе с deny-all для безопасной сети "по умолчанию".

Если нужно разрешить ещё какой-то трафик (например, доступ к API Kubernetes или между сервисами), потребуются дополнительные политики.


```
apiVersion: "cilium.io/v2"
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: "cilium-health-checks"
spec:
  endpointSelector:
    matchLabels:
      'reserved:health': ''
  ingress:
    - fromEntities:
      - remote-node
  egress:
    - toEntities:
      - remote-node

```

Эта политика управляет доступом для проверок здоровья Cilium (cilium-health) между узлами кластера Kubernetes. Она разрешает:

Входящий (ingress) трафик от других узлов (remote-node) к health-эндпоинтам Cilium.

Исходящий (egress) трафик с health-эндпоинтов Cilium к другим узлам.

Структура политики
yaml
apiVersion: cilium.io/v2
kind: CiliumClusterwideNetworkPolicy  # Действует на весь кластер
metadata:
  name: cilium-health-checks  # Название политики
spec:
  endpointSelector:
    matchLabels:
      'reserved:health': ''  # Применяется только к специальным health-подам Cilium
  ingress:
    - fromEntities:
        - remote-node  # Разрешает входящий трафик от других узлов кластера
  egress:
    - toEntities:
        - remote-node  # Разрешает исходящий трафик к другим узлам кластера
Ключевые моменты
endpointSelector

Выбирает только Pod'ы с меткой reserved:health (это специальные эндпоинты Cilium для проверки здоровья сети).

Такие Pod'ы создаются агентом Cilium на каждом узле.

ingress.fromEntities: remote-node

Разрешает входящие подключения от всех других узлов кластера.

Нужно для того, чтобы узлы могли проверять здоровье сети между собой.

egress.toEntities: remote-node

Разрешает исходящие подключения ко всем другим узлам кластера.

Позволяет health-подам инициировать проверки соседних узлов.

Зачем это нужно?
Cilium использует межузловые health-проверки для:

Обнаружения проблем сети (например, если канал между узлами "падает").

Мониторинга состояния кластера (например, в Grafana или Hubble).

Без этой политики (при включённой deny-all) health-проверки не смогут работать, что может привести к ложным срабатываниям и проблемам с маршрутизацией.

Как проверить, что политика работает?
Посмотреть health-статус вручную:

bash
kubectl exec -n kube-system <cilium-agent-pod> -- cilium status
Пример вывода:

Cluster health:   4/4 reachable   (2024-06-10T12:00:00Z)
Проверить метки health-подов:

bash
kubectl get pods -n kube-system -l reserved:health --show-labels
Как интегрируется с другими политиками?
Эта политика дополняет deny-all, добавляя исключение для системного функционала Cilium.

Если нужно ещё больше ограничить доступ (например, только для определённых узлов), можно использовать:

yaml
ingress:
  - fromEntities:
      - remote-node
    fromNodes:
      - matchLabels:
          node-role.kubernetes.io/control-plane: ""  # Только control-plane узлы
Возможные проблемы
Политика не применяется

Убедитесь, что Cilium работает в режиме policy-enforcement=default.

Проверьте логи Cilium:

bash
kubectl logs -n kube-system <cilium-agent-pod>
Health-проверки не работают

Проверьте, что метка reserved:health есть на health-подах:

bash
kubectl get pods -n kube-system -l reserved:health
Вывод
Политика cilium-health-checks.yaml критически важна для:
✅ Корректной работы межузловых проверок здоровья Cilium.
✅ Интеграции с мониторингом (Grafana, Prometheus).
🚀 Должна применяться вместе с deny-all, если используется строгий режим безопасности.


```
vpn-example.yaml

apiVersion: cilium.io/v2alpha1
kind: CiliumCIDRGroup
metadata:
  name: vpn-example-1
  labels:
    role: vpn
spec:
  externalCIDRs:
    - "10.48.0.0/24"
    - "10.16.0.0/24"
```

Этот файл определяет CiliumCIDRGroup — ресурс, который группирует внешние CIDR-блоки (IP-подсети) для удобного использования в Cilium-политиках. В данном случае он создаёт группу vpn-example-1, содержащую две VPN-подсети.

Структура политики
yaml
apiVersion: cilium.io/v2alpha1  # Используется альфа-версия API (может измениться)
kind: CiliumCIDRGroup         # Специальный ресурс для группировки CIDR
metadata:
  name: vpn-example-1         # Уникальное имя группы
  labels:
    role: vpn                 # Произвольная метка для удобства выборки
spec:
  externalCIDRs:              # Список внешних подсетей
    - "10.48.0.0/24"          # Первая VPN-подсеть
    - "10.16.0.0/24"          # Вторая VPN-подсеть
Как это работает?
Группирует CIDR-блоки

Вместо того чтобы указывать подсети напрямую в политиках (CiliumNetworkPolicy), можно ссылаться на группу по имени (vpn-example-1).

Упрощает управление: если подсети изменятся, правки вносятся только в CiliumCIDRGroup.

Используется в политиках
Пример политики, которая разрешает доступ к VPN:

yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-vpn-access
spec:
  endpointSelector:
    matchLabels:
      app: vpn-client
  egress:
    - toCIDRGroup:
        - vpn-example-1  # Разрешает трафик в подсети из группы
Типичные сценарии использования
Доступ к VPN/корпоративным сетям

Группирует внутренние подсети компании, чтобы разрешить доступ Pod'ам.

Геораспределённые сервисы

Можно создать группы для разных регионов (например, europe-cidrs, usa-cidrs).

Временные исключения

Если нужно быстро добавить/удалить подсеть, не меняя все политики.

Как проверить, что группа создана?
bash
kubectl get ciliumcidrgroup
NAME            AGE
vpn-example-1   5m
Ограничения и подводные камни
Альфа-версия API (v2alpha1)

Может измениться в будущих версиях Cilium.

Не заменяет Security Groups

Только маркирует трафик. Для реального ограничения нужны политики.

Нет верификации подсетей

Cilium не проверяет, что указанные подсети действительно доступны.

Интеграция с другими политиками
Пример комбинации с deny-all:

Запрещаем весь трафик (clusterwide-deny-all.yaml).

Разрешаем только VPN через CiliumCIDRGroup:

yaml
egress:
  - toCIDRGroup:
      - vpn-example-1
  - toEntities:
      - world  # Если нужно разрешить ещё и интернет
Вывод
Ресурс CiliumCIDRGroup полезен для:
✅ Упрощения управления списками подсетей в политиках.
✅ Группового применения правил (например, для VPN или гибридных облаков).
🚀 Используйте вместе с CiliumNetworkPolicy для контроля доступа.
