#ifndef CHECKSUM_REPAIR_BJRN_PDTG_CALC_PARSE_H
#define CHECKSUM_REPAIR_BJRN_PDTG_CALC_PARSE_H

//
// Created by Julia on 2019-04-02.
//


struct index_num {
    int index;
    char *number_str;
};

struct index_expr {
    int index;
    char** expr_list;
};

struct index_num parse_num(char* s, int i);

struct index_expr parse_paren(char* s, int i);

struct index_expr parse_expr(char* s, int i);




#endif //CHECKSUM_REPAIR_BJRN_PDTG_CALC_PARSE_H
