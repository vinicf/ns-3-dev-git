build_lib_example(
    NAME sumo-coupling-simple
    SOURCE_FILES sumo-coupling-simple.cc
    LIBRARIES_TO_LINK 
        ${libtraci-applications}
        ${libtraci}
        ${libwifi}
        ${libspectrum}    # CRITICAL: OCB and modern WiFi PHYs need this
        ${libpropagation} # CRITICAL: For signal loss models
        ${libinternet}    # Required for the IP stack in your .cc
        ${libmobility}    # Required for position tracking
        ${libnetanim}
        ${libcore}
        ${libnetwork}
)