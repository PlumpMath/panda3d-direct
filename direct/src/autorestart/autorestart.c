/* Filename: autorestart.c
 * Created by:  drose (05Sep02)
 *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
 *
 * PANDA 3D SOFTWARE
 * Copyright (c) 2001, Disney Enterprises, Inc.  All rights reserved
 *
 * All use of this software is subject to the terms of the Panda 3d
 * Software license.  You should have received a copy of this license
 * along with this source code; you will also find a current copy of
 * the license at http://www.panda3d.org/license.txt .
 *
 * To contact the maintainers of this program write to
 * panda3d@yahoogroups.com .
 *
 * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * */

#include "dtool_config.h"

#ifndef HAVE_GETOPT
#include "gnu_getopt.h"
#else
#include <getopt.h>
#endif

#include <stdio.h>
#include <errno.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <time.h>
#include <signal.h>

char **params = NULL;
char *logfile_name = NULL;
int logfile_fd = -1;

#define TIME_BUFFER_SIZE 128

/* We shouldn't respawn more than (COUNT_RESPAWN - 1) times over
   COUNT_RESPAWN_TIME seconds. */
#define COUNT_RESPAWN 5
#define COUNT_RESPAWN_TIME 30

void
exec_process() {
  /* First, output the command line to the log file. */
  char **p;
  for (p = params; *p != NULL; ++p) {
    fprintf(stderr, "%s ", *p);
  }
  fprintf(stderr, "\n");
  execvp(params[0], params);
  fprintf(stderr, "Cannot exec %s: %s\n", params[0], strerror(errno));

  /* Kill ourselves instead of exiting, to indicate the watching
     process should stop. */
  kill(getpid(), SIGTERM);

  /* Shouldn't get here. */
  exit(1); 
}

int
spawn_process() {
  /* Spawns the child process.  Returns true if the process terminated
     by itself and should be respawned, false if it was explicitly
     killed (or some other error condition exists), and it should not
     respawn any more. */
  pid_t child, wresult;
  int status;

  child = fork();
  if (child < 0) {
    /* Fork error. */
    perror("fork");
    return 0;
  }

  if (child == 0) {
    /* Child.  Exec the process. */
    fprintf(stderr, "Child pid is %d.\n", getpid());
    exec_process();
    /* Shouldn't get here. */
    exit(1);
  }

  /* Parent.  Wait for the child to terminate, then diagnose the reason. */
  wresult = waitpid(child, &status, 0);
  if (wresult < 0) {
    perror("waitpid");
    return 0;
  }

  if (WIFSIGNALED(status)) {
    int signal = WTERMSIG(status);
    fprintf(stderr, "\nprocess caught signal %d.\n\n", signal);
    /* A signal exit is a reason to respawn unless the signal is TERM
       or KILL. */
    return (signal != SIGTERM && signal != SIGKILL);

  } else {
    fprintf(stderr, "\nprocess exited with error code %d.\n\n", WEXITSTATUS(status));
    /* Normal exit is always a reason to respawn. */
    return 1;
  }
}

void
do_autorestart() {
  char time_buffer[TIME_BUFFER_SIZE];
  time_t now;
  time_t count_respawn[COUNT_RESPAWN];
  int cri, num_cri;

  /* Make our process its own process group. */
  setpgid(0, 0);

  /* If we have a logfile, dup it onto stdout and stderr. */
  if (logfile_fd >= 0) {
    dup2(logfile_fd, STDOUT_FILENO);
    dup2(logfile_fd, STDERR_FILENO);
    close(logfile_fd);
  }

  now = time(NULL);
  strftime(time_buffer, TIME_BUFFER_SIZE, "%T on %A, %d %b %Y", localtime(&now));
  fprintf(stderr, "autorestart begun at %s.\n", time_buffer);

  cri = 1;
  num_cri = 1;
  count_respawn[1] = now;
  
  while (spawn_process()) {
    now = time(NULL);

    /* Make sure we're not respawning too fast. */
    cri = (cri + 1) % COUNT_RESPAWN;
    count_respawn[cri] = now;
    if (num_cri < COUNT_RESPAWN) {
      num_cri++;
    } else {
      time_t last = count_respawn[(cri + 1) % COUNT_RESPAWN];
      if (now - last < COUNT_RESPAWN_TIME) {
        fprintf(stderr, "respawning too fast, giving up.\n");
        break;
      }
    }
      
    strftime(time_buffer, TIME_BUFFER_SIZE, "%T on %A, %d %b %Y", localtime(&now));
    fprintf(stderr, "respawning at %s.\n", time_buffer);
  }

  now = time(NULL);
  strftime(time_buffer, TIME_BUFFER_SIZE, "%T on %A, %d %b %Y", localtime(&now));
  fprintf(stderr, "autorestart terminated at %s.\n", time_buffer);
  exit(0);
}

void
double_fork() {
  pid_t child, grandchild, wresult;
  int status;

  /* Fork once, then again, to disassociate the child from the command
     shell process group. */
  child = fork();
  if (child < 0) {
    /* Failure to fork. */
    perror("fork");
    exit(1);
  }

  if (child == 0) {
    /* Child.  Fork again. */
    grandchild = fork();
    if (grandchild < 0) {
      perror("fork");
      exit(1);
    }

    if (grandchild == 0) {
      /* Grandchild.  Begin useful work. */
      do_autorestart();
      /* Shouldn't get here. */
      exit(1);
    }

    /* Child.  Report the new pid, then terminate gracefully. */
    fprintf(stderr, "Spawned, monitoring pid is %d.\n", grandchild);
    exit(0);
  }

  /* Parent.  Wait for the child to terminate, then return. */
  wresult = waitpid(child, &status, 0);
  if (wresult < 0) {
    perror("waitpid");
    exit(1);
  }

  if (!WIFEXITED(status)) {
    if (WIFSIGNALED(status)) {
      fprintf(stderr, "child caught signal %d unexpectedly.\n", WTERMSIG(status));
    } else {
      fprintf(stderr, "child exited with error code %d.\n", WEXITSTATUS(status));
    }
    exit(1);
  }
}

void
usage() {
  fprintf(stderr,
          "\n"
          "autorestart [-l logfilename] program [args . . . ]\n\n");
}

void
help() {
  usage();
  fprintf(stderr,
          "This program is used to run a program as a background task and\n"
          "automatically restart it should it terminate for any reason other\n"
          "than explicit user kill.\n\n"
          "If the program is terminated via a TERM or KILL signal (e.g. via\n"
          "kill [pid] or kill -i [pid]), it is assumed the user meant for the\n"
          "process to stop, and it is not restarted.\n\n");
}

int 
main(int argc, char *argv[]) {
  extern char *optarg;
  extern int optind;
  /* The initial '+' instructs GNU getopt not to reorder switches. */
  static const char *optflags = "+l:h";
  int flag;

  flag = getopt(argc, argv, optflags);
  while (flag != EOF) {
    switch (flag) {
    case 'l':
      logfile_name = optarg;
      break;

    case 'h':
      help();
      return 1;

    case '?':
    case '+':
      usage();
      return 1;

    default:
      fprintf(stderr, "Unhandled switch: -%c\n", flag);
      return 1;
    }
    flag = getopt(argc, argv, optflags);
  }

  argc -= (optind - 1);
  argv += (optind - 1);

  if (argc < 2) {
    fprintf(stderr, "No program to execute given.\n");
    usage();
    return 1;
  }

  params = &argv[1];

  if (logfile_name != NULL) {
    logfile_fd = open(logfile_name, O_WRONLY | O_CREAT | O_TRUNC, 0666);
    if (logfile_fd < 0) {
      fprintf(stderr, "Cannot write to logfile %s: %s\n", 
              logfile_name, strerror(errno));
      return 1;
    }
    fprintf(stderr, "Generating output to %s.\n", logfile_name);
  }

  double_fork();

  return 0;
}

