// Filename: directd.cxx
// Created by:  skyler 2002.04.08
// Based on test_tcp_*.* by drose.
//
////////////////////////////////////////////////////////////////////
//
// PANDA 3D SOFTWARE
// Copyright (c) 2001, Disney Enterprises, Inc.  All rights reserved
//
// All use of this software is subject to the terms of the Panda 3d
// Software license.  You should have received a copy of this license
// along with this source code; you will also find a current copy of
// the license at http://www.panda3d.org/license.txt .
//
// To contact the maintainers of this program write to
// panda3d@yahoogroups.com .
//
////////////////////////////////////////////////////////////////////

#include "directd.h"
/*#include "pandaFramework.h"
#include "queuedConnectionManager.h"*/

//#include <process.h>
//#include <Windows.h>
//#include "pandabase.h"

//#include "queuedConnectionManager.h"
//#include "queuedConnectionListener.h"
//#include "queuedConnectionReader.h"
//#include "connectionWriter.h"
#include "netAddress.h"
#include "connection.h"
#include "datagramIterator.h"
#include "netDatagram.h"

#include "pset.h"



namespace {
  // The following is from an MSDN example:
  
  #define TA_FAILED 0
  #define TA_SUCCESS_CLEAN 1
  #define TA_SUCCESS_KILL 2
  #define TA_SUCCESS_16 3

  BOOL CALLBACK
  TerminateAppEnum(HWND hwnd, LPARAM lParam) {
    DWORD dwID;
    GetWindowThreadProcessId(hwnd, &dwID);
    if(dwID == (DWORD)lParam) {
       PostMessage(hwnd, WM_CLOSE, 0, 0);
    }
    return TRUE;
  }

  /*
      DWORD WINAPI TerminateApp(DWORD dwPID, DWORD dwTimeout)

      Purpose:
        Shut down a 32-Bit Process

      Parameters:
        dwPID
           Process ID of the process to shut down.

        dwTimeout
           Wait time in milliseconds before shutting down the process.

      Return Value:
        TA_FAILED - If the shutdown failed.
        TA_SUCCESS_CLEAN - If the process was shutdown using WM_CLOSE.
        TA_SUCCESS_KILL - if the process was shut down with
           TerminateProcess().
  */ 
  DWORD WINAPI
  TerminateApp(DWORD dwPID, DWORD dwTimeout) {
    HANDLE   hProc;
    DWORD   dwRet;

    // If we can't open the process with PROCESS_TERMINATE rights,
    // then we give up immediately.
    hProc = OpenProcess(SYNCHRONIZE|PROCESS_TERMINATE, FALSE, dwPID);
    if(hProc == NULL) {
       return TA_FAILED;
    }

    // TerminateAppEnum() posts WM_CLOSE to all windows whose PID
    // matches your process's.
    EnumWindows((WNDENUMPROC)TerminateAppEnum, (LPARAM)dwPID);

    // Wait on the handle. If it signals, great. If it times out,
    // then you kill it.
    if(WaitForSingleObject(hProc, dwTimeout)!=WAIT_OBJECT_0) {
       dwRet=(TerminateProcess(hProc,0)?TA_SUCCESS_KILL:TA_FAILED);
    } else {
       dwRet = TA_SUCCESS_CLEAN;
    }
    CloseHandle(hProc);

    return dwRet;
  }

  /*
      Start an application with the command line cmd.
      returns the process id of the new process/application.
  */
  DWORD
  StartApp(const string& cmd) {
    DWORD pid=0;
    STARTUPINFO si; 
    PROCESS_INFORMATION pi; 
    ZeroMemory(&si, sizeof(STARTUPINFO));
    si.cb = sizeof(STARTUPINFO); 
    ZeroMemory(&pi, sizeof(PROCESS_INFORMATION));
    if (CreateProcess(NULL, (char*)cmd.c_str(), 
        0, 0, 1, NORMAL_PRIORITY_CLASS, 
        0, 0, &si, &pi)) {
      pid=pi.dwProcessId;
      CloseHandle(pi.hProcess);
      CloseHandle(pi.hThread);
    } else {
      cerr<<"CreateProcess failed: "<<cmd<<endl;
    }
    return pid;
  }

}


DirectD::DirectD() :
    _host_name("localhost"),
    _port(8001), _app_pid(0),
    _reader(&_cm, 1), _writer(&_cm, 1), _listener(&_cm, 0),
    _verbose(false), _shutdown(false) {
}

DirectD::~DirectD() {
  // Close all the connections:
  ConnectionSet::iterator ci;
  for (ci = _connections.begin(); ci != _connections.end(); ++ci) {
    _cm.close_connection((*ci));
  }
  _connections.clear();
  cerr<<"DirectD dtor"<<endl;
}

int 
DirectD::client_ready(const string& client_host, int port) {
  connect_to(client_host, port);
  send_command("s");
  disconnect_from(client_host, port);
  return 0;
}

bool
DirectD::wait_for_servers(int count, int timeout_ms) {
  if (count <= 0) {
    return true;
  }
  // The timeout is a rough estimate, we may wait slightly longer.
  const wait_ms=200;
  int cycles=timeout_ms/wait_ms;
  while (cycles--) {
    check_for_new_clients();
    check_for_lost_connection();
    /*
        The following can be more generalized with a little work.
        check_for_datagrams() could take a handler function as an arugment, maybe.
    */
    ////check_for_datagrams();
    // Process all available datagrams.
    while (_reader.data_available()) {
      NetDatagram datagram;
      if (_reader.get_data(datagram)) {
        if (_verbose) {
          nout << "Got datagram " /*<< datagram <<*/ "from "
               << datagram.get_address() << endl;
          datagram.dump_hex(nout);
        }
        //handle_datagram(datagram);
        DatagramIterator di(datagram);
        string s=di.get_string();
        cerr<<"wait_for_servers() count="<<count<<", s="<<s<<endl;
        if (s=="r" && !--count) {
          return true;
        }
      }
    }

    // Yield the timeslice before we poll again.
    PR_Sleep(PR_MillisecondsToInterval(wait_ms));
  }
  // We've waited long enough, assume they're not going to be
  // ready in the time we want them:
  return false;
}

int 
DirectD::server_ready(const string& client_host, int port) {
  send_one_message(client_host, port, "r");
  return 0;
}


void
DirectD::start_app(const string& cmd) {
  _app_pid=StartApp(cmd);
}

void
DirectD::kill_app() {
  if (_app_pid) {
    cerr<<"trying k "<<_app_pid<<endl;
    TerminateApp(_app_pid, 1000);
  }
}

void
DirectD::send_command(const string& cmd) {
  NetDatagram datagram;
  datagram.add_string(cmd);
  // Send the datagram.
  ConnectionSet::iterator ci;
  for (ci = _connections.begin(); ci != _connections.end(); ++ci) {
    _writer.send(datagram, (*ci));
  }
}

void
DirectD::handle_datagram(NetDatagram& datagram){
  DatagramIterator di(datagram);
  string cmd=di.get_string();
  handle_command(cmd);
}

void
DirectD::handle_command(const string& cmd) {
  if (_verbose) {
    cerr<<"command: "<<cmd<<endl;
  }
}

void
DirectD::send_one_message(const string& host_name, 
    int port,
    const string& message) {
  NetAddress host;
  if (!host.set_host(host_name, port)) {
    nout << "Unknown host: " << host_name << "\n";
  }

  const int timeout_ms=5000;
  PT(Connection) c = _cm.open_TCP_client_connection(host, timeout_ms);
  if (c.is_null()) {
    nout << "No connection.\n";
    return;
  }

  nout << "Successfully opened TCP connection to " << host_name
       << " on port "
       << c->get_address().get_port() << " and IP "
       << c->get_address() << "\n";

  //_reader.add_connection(c);
  
  NetDatagram datagram;
  datagram.add_string(message);
  _writer.send(datagram, c);
  
  //PR_Sleep(PR_MillisecondsToInterval(200));
  //_reader.remove_connection(c);
  _cm.close_connection(c);
}

void
DirectD::connect_to(const string& host_name, int port) {
  NetAddress host;
  if (!host.set_host(host_name, port)) {
    nout << "Unknown host: " << host_name << "\n";
  }

  const int timeout_ms=5000;
  PT(Connection) c = _cm.open_TCP_client_connection(host, timeout_ms);
  if (c.is_null()) {
    nout << "No connection.\n";
    return;
  }

  nout << "Successfully opened TCP connection to " << host_name
       << " on port "
       << c->get_address().get_port() << " and IP "
       << c->get_address() << "\n";

  _reader.add_connection(c);
  _connections.insert(c);
}

void
DirectD::disconnect_from(const string& host_name, int port) {
  nout<<"disconnect_from(\""<<host_name<<", port="<<port<<")"<<endl;
  for (ConnectionSet::iterator i=_connections.begin(); i != _connections.end(); ++i) {
    nout<<"    found "<<(*i)->get_address().get_ip_string()<<", port "<<(*i)->get_address().get_port()<<endl;
    if ((*i)->get_address().get_ip_string()==host_name) {
      nout<<"    disconnecting."<<endl;
      _reader.remove_connection((*i));
      _cm.close_connection((*i));
      _connections.erase(i);
      break;
    }
  }
}

void
DirectD::check_for_lost_connection() {
  while (_cm.reset_connection_available()) {
    PT(Connection) c;
    if (_cm.get_reset_connection(c)) {
      nout<<"Lost connection from "<<c->get_address()<<endl;
      _connections.erase(c);
      _cm.close_connection(c);
    }
  }
}

void
DirectD::check_for_datagrams(){
  // Process all available datagrams.
  while (_reader.data_available()) {
    NetDatagram datagram;
    if (_reader.get_data(datagram)) {
      if (_verbose) {
        nout << "Got datagram " /*<< datagram <<*/ "from "
             << datagram.get_address() << endl;
        datagram.dump_hex(nout);
      }
      handle_datagram(datagram);
    }
  }
}

void
DirectD::spawn_background_server() {
  stringstream ss;
  ss<<"directd -s "<<_host_name.c_str()<<" "<<_port;
  DWORD serverPID = StartApp(ss.str());
}

void
DirectD::listen_to(int port, int backlog) {
  PT(Connection) rendezvous = _cm.open_TCP_server_rendezvous(_port, backlog);
  if (rendezvous.is_null()) {
    nout << "Cannot grab port " << _port << ".\n";
    exit(1);
  }
  if (_verbose) nout << "Listening for connections on port " << _port << "\n";
  _listener.add_connection(rendezvous);
}

void
DirectD::check_for_new_clients() {
  while (_listener.new_connection_available()) {
    PT(Connection) rv;
    NetAddress address;
    PT(Connection) new_connection;
    if (_listener.get_new_connection(rv, address, new_connection)) {
      if (_verbose) nout << "Got connection from " << address << "\n";
      _reader.add_connection(new_connection);
      _connections.insert(new_connection);
    }
  }
}
