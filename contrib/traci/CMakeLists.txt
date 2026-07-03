# Define the source files for the TraCI module
set(source_files
    model/traci-client.cc
    model/sumo-socket.cc
    model/sumo-storage.cc
    model/sumo-TraCIAPI.cc
)

# Define the header files to be exported to build/include/ns3/
set(header_files
    model/traci-client.h
    model/sumo-TraCIAPI.h
    model/sumo-config.h
    model/sumo-socket.h
    model/sumo-storage.h
    model/sumo-TraCIConstants.h
    model/sumo-TraCIDefs.h
)

# Build the module using the ns-3 CMake macro
build_lib(
    LIBNAME traci
    SOURCE_FILES ${source_files}
    HEADER_FILES ${header_files}
    LIBRARIES_TO_LINK 
        ${libcore}
        ${libmobility}
        ${libinternet}
)
