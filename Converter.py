import json



"""   Convert pygmalion file to specified format   """

def convert_pygmalion(file):

    methods={} #helper dict method_name->id

    method_dict = {} #dict for method_id->(method_id, name, children)

    # irelevant input comparisions
    irrelevant_operators = ["tokenstore", "tokencomp", "EOF"]

    input_comparisons = []


    with open(file) as json_file:

        for line in json_file:

            #ignore comments
            if not line.startswith("{"):
                continue

            data = json.loads(line)

            '''build tree of invocations'''
            if data['type'] == "STACK_EVENT":
                stack = data['stack']
                parent_id = 0
                for method in stack:
                    if method in methods.keys():
                        parent_id = methods[method]
                        continue

                    else:
                        method_id = len(methods) #starts with 0
                        methods[method] = method_id
                        method_dict[method_id] = (method_id, method, [])
                        if method_id > 0:
                            method_dict[parent_id][2].append(method_id)

            '''build list of comparisions'''
            if data['type'] == "INPUT_COMPARISON":

                operator = data['operator']

                if operator in irrelevant_operators:
                    continue

                index = data['index'][0] # !! for strcmp there is a list of indeces. Only taken first one.
                method = data['stack'][-1]
                method_id = methods[method] #get id from helper dict

                input_comparisons.append((index, method_id))

    #write json files
    with open("my_method_map.json", 'w+') as cfile:
        json.dump(method_dict, cfile)

    with open("my_comparisons.json", 'w+') as mfile:
        json.dump(input_comparisons, mfile)


if __name__ == "__main__":

    convert_pygmalion("pygmalion.json")


