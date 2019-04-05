//
// Created by Julia on 2019-04-02.
//

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "stdbool.h"
#include "calc_parse.h"

struct index_num parse_num(char* s, int i){

    printf("Entering parse_num...\n");

    struct index_num result;

    char* buf = (char*) malloc((strlen(s)-i) * sizeof(char)); //

    for (int j=0; j<strlen(s); j++){
        if (!isdigit(s[i])){
            break;
        } else {
            buf[j] = s[i];
            i++;
        }
    }

    result.index = i;
    result.number_str = strdup(buf);

    printf("Leaving parse_num...\n");

    return result;

}


struct index_expr parse_paren(char* s, int i) {

    printf("Entering parse_paren...\n");


    if (s[i] != '('){
        printf("parse paren without '(' in the beginning.\n");
    } else {

        struct index_expr result;
        result = parse_expr(s, i+1);

        if (result.index > strlen(s)){
            printf("Warning: index greater than string len!\n");
        }

        if (s[result.index] == ' '){
            printf("Error '' parse_paren.\n");
        } else {

            if (s[result.index] != ')'){
                printf("Missing closing paren!\n");

            } else {
                result.index += 1;
                printf("Leaving parse_paren...\n");
                return result;
            }
        }
    }
}


/*
 *
 * ATTENTION:
 * Return values not correct yet.
 *
 */

struct index_expr parse_expr(char* s, int i) {

    printf("Entering parse_expr...\n");


    struct index_expr expressions;

    expressions.expr_list = (char**) malloc((strlen(s)-i)* sizeof(char*));

    char** expr = expressions.expr_list;

    struct index_num number;
    struct index_expr paren;


    while ( i < strlen(s)){
        char c = s[i];
        if (isdigit(c)){
            number = parse_num(s, i);
            i = number.index; //set new index in input string
            *expr = number.number_str; //=expr.append(number)
            expr++;
        }

        else if (c == '+' || c == '-' || c == '*' || c == '/'){
            //
            char str[2];
            str[0] = c;
            //string always ends with a null character
            str[1] = '\0';
            *expr = str;
            expr++;
            i++;
        }
        else if (c == '('){
            paren = parse_paren(s, i);
            i = paren.index; //-.-

            *expr = *paren.expr_list; //### this doesn't work if it's a list of expressions instead of char*

            expr++;

        }
        else if (c == ')'){
            expressions.index = i;
            printf("Leaving parse_expr...\n");
            return expressions;
        }

    }

    expressions.index = i;
    printf("Leaving parse_expr...\n");
    return expressions;

}


int main(int argc, char *argv[])
{

    //struct index_expr result;

    //result = parse_expr("(10+2)", 0);

    char my_string[10000];

    if (argc == 1){
        //for use with echo "URL"
        //TODO inifinite loop when no input...
        fgets(my_string, sizeof(my_string) - 1, stdin);

        if (!strcmp(&my_string[strlen(my_string)-1], "\n")){
            my_string[strlen(my_string)-1] = 0; //remove newline character from fgets() at the end of string
        }

    } else {
        //for standard use ./calc URL
        strcpy(my_string, argv[1]);
    }

    parse_expr(my_string, 0);
}

