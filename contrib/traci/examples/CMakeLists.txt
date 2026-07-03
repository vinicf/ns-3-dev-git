build_lib_example(
    NAME traci-example
    SOURCE_FILES traci-example.cc
    LIBRARIES_TO_LINK 
        ${libtraci}
        ${libcore}
        ${libnetwork}
)