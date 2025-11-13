1. Проверка текущего состояния
Сначала проверь, какая версия cgroup используется:

bash
# Проверить версию cgroup
mount | grep cgroup
cat /proc/filesystems | grep cgroup

# Или более современный способ
stat -fc %T /sys/fs/cgroup/
2. Проверка поддержки ядром
Убедись, что ядро поддерживает cgroup v2:

bash
# Проверить поддержку cgroup v2
grep cgroup /proc/filesystems
cat /sys/kernel/cgroup_features

# Проверить параметры ядра
cat /boot/config-$(uname -r) | grep CGROUP
3. Временное переключение (для тестирования)
Для тестирования можно временно переключиться:

bash
# Добавить параметры ядра
sudo grubby --update-kernel=ALL --args="systemd.unified_cgroup_hierarchy=1"

# Или через GRUB в /etc/default/grub:
# GRUB_CMDLINE_LINUX="systemd.unified_cgroup_hierarchy=1"
4. Постоянное включение cgroup v2
Для systemd систем:
bash
# Добавить параметры ядра
sudo grubby --update-kernel=ALL --args="systemd.unified_cgroup_hierarchy=1"

# Обновить конфигурацию GRUB (для некоторых дистрибутивов)
sudo update-grub

# Перезагрузить
sudo reboot
Проверить после перезагрузки:
bash
mount | grep cgroup
# Должно показывать cgroup2
5. Проверка миграции systemd
bash
# Проверить версию cgroup systemd
systemd-detect-virt --cgroup

# Посмотреть иерархию
systemd-cgls

# Проверить метрики
systemd-cgtop
6. Настройка Docker/Kubernetes
Docker:
bash
# Создать конфиг
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<EOF
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m"
  },
  "storage-driver": "overlay2"
}
EOF

# Перезапустить Docker
sudo systemctl restart docker
Kubernetes:
yaml
# kubelet configuration
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
cgroupDriver: systemd
7. Проверка приложений
Убедись, что приложения работают корректно:

bash
# Проверить cgroup процесса
cat /proc/self/cgroup

# Тестовый контейнер
docker run --rm alpine cat /proc/self/cgroup
8. Обратная миграция (если нужно)
Если возникнут проблемы:

bash
sudo grubby --update-kernel=ALL --remove-args="systemd.unified_cgroup_hierarchy=1"
sudo reboot
9. Полезные команды для мониторинга
bash
# Просмотр cgroup
ls -la /sys/fs/cgroup/

# Мониторинг ресурсов
cat /sys/fs/cgroup/system.slice/memory.current
cat /sys/fs/cgroup/system.slice/cpu.stat

# Современные инструменты
systemd-analyze blame
cgroup-v2
