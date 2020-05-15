import pdb
import pprint
import re
from datadog import api

# all_id_list returns a list of all id's found in an api resource's get_all() response
def all_id_list(resp, resource):
    id_list = []

    if resource == "dash":
        id_list = [d['id'] for d in resp.get("dashboards")]
    elif resource == "monitor":
        id_list = [m['id'] for m in resp]
    else:
        print(resource + " is an invalid resource name, exiting.")
        quit()

    return id_list

# metric_report outputs a list of where metrics are being used in your Datadog account
def metric_report(ids_list, metrics_to_eval, resource):
    title = ''
    resp = {}
    query = ''
    getter = ''

    backend_regexp = re.compile(r'by \{.*?backend.*?\}')

    for id in ids_list:
        if resource == "dash":
            resp = api.Dashboard.get(str(id))
            query = str(resp.get("widgets"))
            getter = "title"
            url = 'https://app.datadoghq.com' + resp.get('url')
            extra = []
            # resp['widgets'][0]['definition']['requests'][0]['q']
            for widget in resp['widgets']:
                # ugh this tuple could get long
                if widget['definition']['type'] in ('free_text', 'toplist', 'heatmap', 'hostmap', 'iframe', 'note', 'query_table', 'change', 'check_status', 'relative', 'distribution', 'manage_status', 'alert_value', 'slo', 'treemap', 'event_stream', 'event_timeline', 'image', 'alert_graph', 'log_stream', 'scatterplot'):
                    continue
                elif widget['definition']['type'] in ('timeseries', 'query_value'):
                    for request in widget['definition']['requests']:
                        if any(k in request for k in ('apm_query', 'log_query', 'process_query')):
                            continue
                        try:
                            if backend_regexp.search(request['q']):
                                extra.append(request['q'])
                        except KeyError as e:
                            pprint.pprint(request)
                            raise e
                elif widget['definition']['type'] == 'group':
                    for group_widgets in widget['definition']['widgets']:
                        if 'requests' not in group_widgets['definition']:
                            continue
                        for group_widget_request in group_widgets['definition']['requests']:
                            if isinstance(group_widget_request, str):
                                continue
                            else:
                                if any(k in group_widget_request for k in ('apm_query', 'log_query', 'process_query')):
                                    continue
                                try:
                                    if backend_regexp.search(group_widget_request['q']):
                                        extra.append(group_widget_request['q'])
                                except KeyError as e:
                                    pprint.pprint(group_widget_request)
                                    raise e
                else:
                    print(f'Unknown widget type: {widget["definition"]["type"]}')
                    pprint.pprint(widget)

        elif resource == "monitor":
            for i in range(0,100):
                while True:
                    try:
                        resp = api.Monitor.get(str(id))
                    except api.exceptions.HTTPError:
                        print("HTTPError. Retrying...")
                        continue
                    break

            query = str(resp.get("query"))
            getter = "name"
            url = 'https://app.datadoghq.com/monitors#{id}'.format(id=resp.get('id'))
            extra = None
        else:
            print(resource + " is an invalid resource name, exiting.")
            quit()

        for metric in metrics_to_eval:
                if query.find(metric) != -1:
                    if resource == "dash" and not extra:
                        continue

                    if title != resp[getter]:
                        title = resp[getter]
                        print('\n\tTitle: ' + resp[getter])
                        print(f'\t\t{url}')
                        if extra:
                            print('\t\t' + str(extra))
                    print('\t\t  Metric: ' + metric)



# dashboard has a "url" attribute
# monitors have "id" and URL pattern: https://app.datadoghq.com/monitors#11088524
