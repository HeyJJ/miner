#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "stdbool.h"
#define MAX_STR_SIZE 10000

typedef struct str {
  char my_string[MAX_STR_SIZE];
  int idx;
} my_arg;

void parse_num(my_arg *arg);
void parse_expr(my_arg *arg);
void parse_paren(my_arg *arg);
int nesting = 0;

void tab_enter(char* proc, my_arg* arg) {
  for (int i = 0; i < nesting; i++)fprintf(stderr, "\t"); fprintf(stderr,"-> %s %d\n", proc, arg->idx);
  nesting += 1;
}

void tab_exit(char* proc, my_arg* arg) {
  nesting -= 1;
  for (int i = 0; i < nesting; i++)fprintf(stderr,"\t"); fprintf(stderr,"<- %s %d\n", proc, arg->idx);
}

void parse_num(my_arg *arg) {
  tab_enter("parse_num", arg);
  for (;arg->idx < strlen(arg->my_string); arg->idx++) {
    if (!isdigit(arg->my_string[arg->idx])) {
      break;
    }
  }
  tab_exit("parse_num", arg);
  return;
}

void parse_paren(my_arg *arg) {
  tab_enter("parse_paren", arg);
  if (arg->my_string[arg->idx] != '(') {
    printf("Invalid parse!\n");
    tab_exit("parse_paren", arg);
    return;
  }
  arg->idx += 1;
  parse_expr(arg);
  if (arg->my_string[arg->idx] != ')') {
    printf("Missing closing paren!\n");
    tab_exit("parse_paren", arg);
    return;
  }
  arg->idx += 1;
  tab_exit("parse_paren", arg);
}

void parse_expr(my_arg *arg) {
  tab_enter("parse_expr", arg);
  while (arg->idx < strlen(arg->my_string)) {
    char c = arg->my_string[arg->idx];
    if (isdigit(c)) {
      parse_num(arg);
    } else if (c == '+' || c == '-' || c == '*' || c == '/') {
      arg->idx += 1;
    } else if (c == '(') {
      parse_paren(arg);
    } else if (c == ')') {
      break;
    }
  }
  tab_exit("parse_expr", arg);
}

int main(int argc, char *argv[]) {
  my_arg arg;
  if (argc == 1) {
    fgets(arg.my_string, MAX_STR_SIZE-1, stdin);
    arg.idx = 0;
    int l = strlen(arg.my_string);
    if (!strcmp(&arg.my_string[l-1], "\n")){
      arg.my_string[l-1] = 0; //remove newline character from fgets() at the end of string
    }
  } else {
    strcpy(arg.my_string, argv[1]);
    arg.idx = 0;
    printf("%p-%p\n", arg.my_string, arg.my_string + sizeof(arg.my_string));
  }
  parse_expr(&arg);
}
