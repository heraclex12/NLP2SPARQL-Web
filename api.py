from generator_utils import query_dbpedia, decode

if __name__ == '__main__':
    cnt = 0
    n_has_result = 0
    n_no_result = 0
    out_file = open('LCQUAD/no_result_out.txt', 'w', encoding='utf-8')
    out_file2 = open('LCQUAD/has_result_out.txt', 'w', encoding='utf-8')
    with open('LCQUAD/1200/test_1.output', 'r', encoding='utf-8') as file:
        for line in file:
            idx, sparql_query = line.strip().split('\t')
            decoded_sparql_query = decode(sparql_query)
            results = query_dbpedia(decoded_sparql_query)
            if 'results' in results and not results['results']['bindings']:
                out_file.write(idx + '\t' + decoded_sparql_query + '\n')
                n_no_result += 1
            else:
                n_has_result += 1
                if 'boolean' in results:
                    out_file2.write(idx + '\t' + str(results['boolean']*1) + '\t' + decoded_sparql_query + '\n')
                    continue
                if len(results['results']['bindings']) > 1:
                    print(results['results']['bindings'])
                    # break

                out_file2.write(idx + '\t' + list(results['results']['bindings'][0].values())[0]['value'] + '\t' + decoded_sparql_query + '\n')

        print(n_no_result, n_has_result)
    out_file.close()
    out_file2.close()