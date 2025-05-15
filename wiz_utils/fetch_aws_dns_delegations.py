import base64
import json
import requests
import os

'''Wiz API credentials consist of client ID & Secret and Headers'''
HEADERS_AUTH = {"Content-Type": "application/x-www-form-urlencoded"}
HEADERS = {"Content-Type": "application/json"}
CLIENT_ID = os.getenv("wiz-client-id")
CLIENT_SECRET = os.getenv("wiz-client-secret")

'''A GraphQL that used to setup the query. Resulting with search timeframe, status of issues, etc.'''
QUERY = """
    query GraphSearch($query: GraphEntityQueryInput, $controlId: ID, $projectId: String!, $first: Int, $after: String, $fetchTotalCount: Boolean!, $quick: Boolean = true, $fetchPublicExposurePaths: Boolean = false, $fetchInternalExposurePaths: Boolean = false, $fetchIssueAnalytics: Boolean = false, $fetchLateralMovement: Boolean = false, $fetchCodeSource: Boolean = false, $fetchKubernetes: Boolean = false, $fetchCost: Boolean = false, $issueId: ID) {
      graphSearch(
        query: $query
        controlId: $controlId
        projectId: $projectId
        first: $first
        after: $after
        quick: $quick
        issueId: $issueId
      ) {
        totalCount @include(if: $fetchTotalCount)
        maxCountReached @include(if: $fetchTotalCount)
        pageInfo {
          endCursor
          hasNextPage
        }
        nodes {
          entities {
            deletedAt
            isRestricted
            ...PathGraphEntityFragment
            userMetadata {
              isInWatchlist
              isIgnored
              note
            }
            technologies {
              id
              icon
            }
            cost(
              filterBy: {timestamp: {inLast: {amount: 30, unit: DurationFilterValueUnitDays}}}
            ) @include(if: $fetchCost) {
              amortized
              blended
              unblended
              netAmortized
              netUnblended
              currencyCode
            }
            costImpact @include(if: $fetchCost) {
              monthly
            }
            publicExposures(first: 10) @include(if: $fetchPublicExposurePaths) {
              nodes {
                ...NetworkExposureFragment
              }
            }
            otherSubscriptionExposures(first: 10) @include(if: $fetchInternalExposurePaths) {
              nodes {
                ...NetworkExposureFragment
              }
            }
            otherVnetExposures(first: 10) @include(if: $fetchInternalExposurePaths) {
              nodes {
                ...NetworkExposureFragment
              }
            }
            lateralMovementPaths(first: 10) @include(if: $fetchLateralMovement) {
              nodes {
                id
                pathEntities {
                  entity {
                    ...PathGraphEntityFragment
                  }
                }
              }
            }
            codeSourcePath(first: 10) @include(if: $fetchCodeSource) {
              totalCount
              nodes {
                id
                pathEntities {
                  ...PathGraphEntityFragment
                }
              }
            }
            kubernetesPaths(first: 10) @include(if: $fetchKubernetes) {
              nodes {
                id
                path {
                  ...PathGraphEntityFragment
                }
              }
            }
          }
          aggregateCount
        }
      }
    }
    
        fragment PathGraphEntityFragment on GraphEntity {
      id
      name
      type
      properties
      issueAnalytics: issues(filterBy: {status: [IN_PROGRESS, OPEN]}) @include(if: $fetchIssueAnalytics) {
        highSeverityCount
        criticalSeverityCount
      }
    }
    

        fragment NetworkExposureFragment on NetworkExposure {
      id
      portRange
      sourceIpRange
      destinationIpRange
      path {
        ...PathGraphEntityFragment
      }
      applicationEndpoints {
        ...PathGraphEntityFragment
      }
    }
"""

'''Variables used in collaboration with the query, configure the search criteria, project IDs, pagination, number of results, etc.'''
VARIABLES = {
  "quick": False,
  "fetchPublicExposurePaths": True,
  "fetchInternalExposurePaths": False,
  "fetchIssueAnalytics": False,
  "fetchLateralMovement": True,
  "fetchCodeSource": True,
  "fetchKubernetes": False,
  "fetchCost": False,
  "first": 500,
  "query": {
    "relationships": [
      {
        "type": [
          {
            "type": "OWNS"
          }
        ],
        "with": {
          "select": True,
          "type": [
            "DNS_RECORD"
          ],
          "where": {
            "type": {
              "EQUALS": [
                "NS"
              ]
            }
          }
        }
      }
    ],
    "select": True,
    "type": [
      "DNS_ZONE"
    ],
    "where": {
      "nativeType": {
        "EQUALS": [
          "dnsZone"
        ]
      }
    }
  },
  "projectId": "*",
  "fetchTotalCount": False
}

def query_wiz_api(query, variables, dc):
    """This function Query Wiz API for the graphql query
    :param query: the grapql query used to fetch results
    :param variables: the configured query sent along with the query to fetch the results
    :param dc: Value returned alongside the API token from Wiz that indicates which region, endpoint, or account context the token applies to."""

    data = {"variables": variables, "query": query}

    try:
        result = requests.post(url=f"https://api.{dc}.app.wiz.io/graphql",
                               json=data, headers=HEADERS, timeout=180)

    except requests.exceptions.HTTPError as e:
        print(f"<p>Wiz-API-Error (4xx/5xx): {str(e)}</p>")
        return e

    except requests.exceptions.ConnectionError as e:
        print(f"<p>Network problem (DNS failure, refused connection, etc): {str(e)}</p>")
        return e

    except requests.exceptions.Timeout as e:
        print(f"<p>Request timed out: {str(e)}</p>")
        return e

    return result.json()


def request_wiz_api_token(client_id, client_secret):
    """Retrieve token to query the Wiz API.
    :param client_id: the client id used in the API
    :param client_secret: secret used in the API"""

    auth_payload = {
      'grant_type': 'client_credentials',
      'audience': 'wiz-api',
      'client_id': client_id,
      'client_secret': client_secret
    }
    try:
        response = requests.post(url="https://auth.app.wiz.io/oauth/token",
                                headers=HEADERS_AUTH, data=auth_payload, timeout=180)

    except requests.exceptions.HTTPError as e:
        print(f"<p>Error authenticating to Wiz (4xx/5xx): {str(e)}</p>")
        return e

    except requests.exceptions.ConnectionError as e:
        print(f"<p>Network problem (DNS failure, refused connection, etc): {str(e)}</p>")
        return e

    except requests.exceptions.Timeout as e:
        print(f"<p>Request timed out: {str(e)}</p>")
        return e

    try:
        response_json = response.json()
        token = response_json.get('access_token')
        if not token:
            message = f"Could not retrieve token from Wiz: {response_json.get('message')}"
            raise ValueError(message)
    except ValueError as exception:
        message = f"Could not parse API response {exception}. Check Service Account details " \
                    "and variables"
        raise ValueError(message) from exception

    response_json_decoded = json.loads(
        base64.standard_b64decode(pad_base64(token.split(".")[1]))
    )

    response_json_decoded = json.loads(
        base64.standard_b64decode(pad_base64(token.split(".")[1]))
    )
    dc = response_json_decoded["dc"]

    return token, dc


def pad_base64(data):
    """Makes sure base64 data is padded
    :param data: the data used in the API that being encoded"""
    missing_padding = len(data) % 4
    if missing_padding != 0:
        data += "=" * (4 - missing_padding)
    return data


def main():
    """Main function"""

    print("Getting token.")
    token, dc = request_wiz_api_token(CLIENT_ID, CLIENT_SECRET)
    HEADERS["Authorization"] = "Bearer " + token

    result = query_wiz_api(QUERY, VARIABLES, dc)
    print(result)  #DATA IS HERE

    pageInfo = result['data']['graphSearch']['pageInfo']
    while (pageInfo['hasNextPage']): #FETCH NEXT PAGE
        VARIABLES['after'] = pageInfo['endCursor']
        result = query_wiz_api(QUERY, VARIABLES, dc)
        print(result)
        pageInfo = result['data']['graphSearch']['pageInfo']


if __name__ == '__main__':
    main()
    