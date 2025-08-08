"""
GitLB pipeline linter via API
"""

import os
import logging
import sys
import json
import yaml
import gitlab


def main():
    logging.info('Starting script')

    try:
        gitlab_token = os.environ['GITLAB_TOKEN']
        gitlab_project_id = os.environ['GITLAB_PROJECT_ID']
        gitlab_url = os.environ['CI_SERVER_URL']
        project_path = os.environ['CI_PROJECT_PATH']
        current_branch = os.environ['CI_COMMIT_REF_NAME']
    except KeyError as e:
        logging.error('Environment variable not set: %s', e)
        sys.exit(1)

    general_pipeline_dir = './entry-point'
    general_pipeline_files = map(lambda x: os.path.join(general_pipeline_dir, x), filter(lambda x: x.endswith('.yml'), os.listdir(general_pipeline_dir)))
    gitlab_interface = gitlab.Gitlab(gitlab_url, private_token=gitlab_token)
    project_interface = gitlab_interface.projects.get(gitlab_project_id)

    error_flag = False
    for general_pipeline_file in general_pipeline_files:
        with open(general_pipeline_file, 'r', encoding='utf-8') as f:
            pipeline_file = yaml.load(f, Loader=yaml.FullLoader)
            if 'include' not in pipeline_file:
                logging.error('No include statement found in %s', general_pipeline_file)
                error_flag = True

        pipeline_data_ref = {
            'include': [
                {
                    'project': project_path,
                    'ref': current_branch,
                    'file': [include_file['local'] for include_file in pipeline_file['include']]
                }
            ],
        }

        data = {
            'content': json.dumps(pipeline_data_ref),
        }

        lint_result = project_interface.ci_lint.create(data)
        if not lint_result.valid:
            logging.error('Pipeline file %s is not valid', general_pipeline_file)
            error_flag = True
        else:
            logging.info('Pipeline file %s is valid', general_pipeline_file)

    if error_flag:
        sys.exit(1)

if __name__ == '__main__':
    main()
