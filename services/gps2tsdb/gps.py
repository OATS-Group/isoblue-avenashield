#!/usr/bin/python3
from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop
import dbus
import postgres
import os
from prometheus_client import start_http_server, Gauge

def fix(*args):
    #print(args)
    print("Time: ", args[0], "\tLat: ", args[3], "\tLng: ", args[4])
    lat_gauge.set(args[3])
    lng_gauge.set(args[4])
    time_gauge.set(args[0])

    print("Inserting lat and lng for timestanp ", args[0])
    db.run("INSERT INTO gps (time, lat, lng) VALUES (to_timestamp(%s), %s, %s)", (float(args[0]), float(args[3]), float(args[4]) ) )
    print("Finsihed inserting lat and lng for timestamp ", args[0])

global lat_gauge
lat_gauge = Gauge('avena_position_lat', 'Last know fix latitude')
global lng_gauge
lng_gauge = Gauge('avena_position_lng', 'Last know fix longitude')
global time_gauge
time_gauge = Gauge('avena_position_time', 'Last know fix time')
start_http_server(10001)

global db
connectionurl='postgresql://' + os.environ['db_user'] + ':' + os.environ['db_password'] + '@postgres:' + os.environ['db_port'] + '/' + os.environ['db_database']
print("Initing Postgres obj")
db = postgres.Postgres(url=connectionurl)

print("Ensuring timescaledb extension is activated")
db.run("CREATE EXTENSION IF NOT EXISTS timescaledb;")
print("Ensuring tables are setup properly")
db.run("""
        CREATE TABLE IF NOT EXISTS gps (
          time timestamptz UNIQUE NOT NULL,
          lat double precision NOT NULL,
          lng double precision NOT NULL);""")
print("Ensuring GPS point table is a timescaledb hypertable")
db.run("SELECT create_hypertable('gps', 'time', if_not_exists => TRUE, migrate_data => TRUE);")
print("Finished settting up tables")


DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
bus.add_signal_receiver(fix, signal_name='fix', dbus_interface="org.gpsd")

loop = GLib.MainLoop()
loop.run()
