cmake_minimum_required(VERSION 3.8)
project(go2_slam)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

install(DIRECTORY config/
  DESTINATION share/${PROJECT_NAME}/config
)

install(PROGRAMS
  scripts/unitree_odom_to_tf.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
