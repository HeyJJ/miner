//
// Created by Julia on 2019-04-02.
//

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include "stdbool.h"
#include "calc_example.h"

struct index_num parse_num(char* s, int i){

    struct index_num result;

    result.number_str = (char *) malloc(100*sizeof(char));
    char* cur = result.number_str;

    for (int j=0; j<strlen(s); j++){
        if (!isdigit(s[i])){
            break;
        } else {
            cur[j] = s[i];
            i++;
        }
    }

    result.index = i;
    return result;

}


struct index_expr parse_paren(char* s, int i) {


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
                printf("parse paren done, expr last: %s \n", result.expr_list[2]);
                return result;
            }
        }
    }
}

struct index_expr parse_expr(char* s, int i) {

    struct index_expr expressions;
    expressions.expr_list = (char**) malloc(1000* sizeof(char));

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
            return expressions;
        }

    }

    expressions.index = i;
    return expressions;

}



int main(int argc, char *argv[])
{

    /*char *myString;

    printf("argc: %d \n", argc);

    if (argc < 2){
        myString = "(25-1/(2+3))*100/3";
    } else {
        myString = argv[1];
    }*/

    struct index_expr result;

    result = parse_expr("(10+2)", 0);

    for (int i = 0; i < 3; i++){
        printf("%s \n",result.expr_list[i]);

    }

}

