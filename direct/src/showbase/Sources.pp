#begin lib_target
  #define TARGET showbase
  #define LOCAL_LIBS \
    directbase
  #define OTHER_LIBS \
    linmath:c putil:c panda:m express:c pandaexpress:m dtoolconfig dtool

  #define SOURCES \
    showBase.cxx showBase.h

  #define IGATESCAN all
#end lib_target

#define INSTALL_SCRIPTS ppython
