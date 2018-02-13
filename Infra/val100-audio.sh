#! /bin/sh
### BEGIN INIT INFO
# Provides:          val100-audio
# Required-Start:
# Required-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Activates audio for val100
# Description:
### END INIT INFO

do_start () {
        echo 125 > /sys/class/gpio/export
        echo out > /sys/class/gpio/gpio125/direction
        echo 1 > /sys/class/gpio/gpio125/value
        echo -1 > /sys/devices/soc0/sound-sgtl5000.24/HiFi/pmdown_time
        echo "Audio activated on val100"
}

case "$1" in
  start)
        do_start
        ;;
  restart|reload|force-reload)
        do_start
        ;;
  stop)
        # No-op
        ;;
  status)
        exit 0
        ;;
  *)
        echo "Usage: $0 start|restart|reload|force-reload" >&2
        exit 3
        ;;
esac