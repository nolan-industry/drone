#!/usr/bin/env python

from __future__ import print_function
from dronekit import connect, VehicleMode
import time

print("connecting to sitl copter")
vehicle = connect('tcp:127.0.0.1:5763', wait_ready=True)
vehicle.wait_ready('autopilot_version')

print("\nGet all vehicle attribute values:")
print(" Autopilot Firmware version: %s" % vehicle.version)
print("   Major version number: %s" % vehicle.version.major)
print("   Minor version number: %s" % vehicle.version.minor)
print("   Patch version number: %s" % vehicle.version.patch)
print("   Release type: %s" % vehicle.version.release_type())
print("   Release version: %s" % vehicle.version.release_version())
print("   Stable release?: %s" % vehicle.version.is_stable())
print(" Autopilot capabilities")
print("   Supports MISSION_FLOAT message type: %s" % vehicle.capabilities.mission_float)
print("   Supports PARAM_FLOAT message type: %s" % vehicle.capabilities.param_float)
print("   Supports MISSION_INT message type: %s" % vehicle.capabilities.mission_int)
print("   Supports COMMAND_INT message type: %s" % vehicle.capabilities.command_int)
print("   Supports PARAM_UNION message type: %s" % vehicle.capabilities.param_union)
print("   Supports ftp for file transfers: %s" % vehicle.capabilities.ftp)
print("   Supports commanding attitude offboard: %s" % vehicle.capabilities.set_attitude_target)
print("   Supports commanding position and velocity targets in local NED frame: %s" % vehicle.capabilities.set_attitude_target_local_ned)
print("   Supports set position + velocity targets in global scaled integers: %s" % vehicle.capabilities.set_altitude_target_global_int)
print("   Supports terrain protocol / data handling: %s" % vehicle.capabilities.terrain)
print("   Supports direct actuator control: %s" % vehicle.capabilities.set_actuator_target)
print("   Supports the flight termination command: %s" % vehicle.capabilities.flight_termination)
print("   Supports mission_float message type: %s" % vehicle.capabilities.mission_float)
print("   Supports onboard compass calibration: %s" % vehicle.capabilities.compass_calibration)
print(" Global Location: %s" % vehicle.location.global_frame)
print(" Global Location (relative altitude): %s" % vehicle.location.global_relative_frame)
print(" Local Location: %s" % vehicle.location.local_frame)
print(" Attitude: %s" % vehicle.attitude)
print(" Velocity: %s" % vehicle.velocity)
print(" GPS: %s" % vehicle.gps_0)
print(" Gimbal status: %s" % vehicle.gimbal)
print(" Battery: %s" % vehicle.battery)
print(" EKF OK?: %s" % vehicle.ekf_ok)
print(" Last Heartbeat: %s" % vehicle.last_heartbeat)
print(" Rangefinder: %s" % vehicle.rangefinder)
print(" Rangefinder distance: %s" % vehicle.rangefinder.distance)
print(" Rangefinder voltage: %s" % vehicle.rangefinder.voltage)
print(" Heading: %s" % vehicle.heading)
print(" Is Armable?: %s" % vehicle.is_armable)
print(" System status: %s" % vehicle.system_status.state)
print(" Groundspeed: %s" % vehicle.groundspeed)    # settable
print(" Airspeed: %s" % vehicle.airspeed)    # settable
print(" Mode: %s" % vehicle.mode.name)    # settable
print(" Armed: %s" % vehicle.armed)    # settable

def arm_and_takeoff(aTargetAltitude):
    print("basic pre-arm checks")
    while not vehicle.is_armable:
        print("wait for vehicle to initialise..")
        time.sleep(1)

    print("Arming motors")
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:
        print("waiting for arming...")
        time.sleep(1)

    print("Taking off")
    vehicle.simple_takeoff(aTargetAltitude)

    while True:
        print("Altitude:", vehicle.location.global_relative_frame.alt)
        if vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.95:
            print("reached target altitude")
            break
        time.sleep(1)

arm_and_takeoff(10)

print("set default/target airspeed to 3")
vehicle.airspeed = 3

print("going towards 1st point for 30secs...")
waypoint1 = LocationGlobalRelative(-35.361354, 149.165218, 20)
vehicle.simple_goto(waypoint1)

time.sleep(30)

print('going to 2nd point for 30 secs (groundspeed set to 10m/s')
waypoint2 = LocationGlobalRelative(-35.363244, 149.168801, 20)
vehicle.simple_goto(waypoint2, groundspeed=10)

time.sleep(30)

vehicle.mode = VehicleMode("RTL")

print('close vehicle object')
vehicle.close()
