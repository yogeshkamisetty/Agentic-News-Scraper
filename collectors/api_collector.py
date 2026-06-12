import os

import requests


PRODUCTHUNT_API_URL = "https://api.producthunt.com/v2/api/graphql"


def collect_producthunt(
    limit=20,
    timeout=8
):
    """
    Collect Product Hunt AI launches when PRODUCTHUNT_TOKEN is configured.
    Returns an empty list without failing the pipeline if credentials are absent.
    """

    token = os.environ.get(
        "PRODUCTHUNT_TOKEN",
        ""
    ).strip()

    if not token:
        return []

    query = """
    query AgenticNewsEngineProductHunt($first: Int!) {
      posts(first: $first, topic: "artificial-intelligence", order: VOTES) {
        edges {
          node {
            name
            tagline
            votesCount
            commentsCount
            url
            createdAt
          }
        }
      }
    }
    """

    try:
        response = requests.post(
            PRODUCTHUNT_API_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "variables": {
                    "first": limit
                },
            },
            timeout=timeout
        )

        response.raise_for_status()
        payload = response.json()

    except Exception as exc:
        print(
            f"Product Hunt warning: {str(exc)[:120]}"
        )
        return []

    if payload.get("errors"):
        print(
            f"Product Hunt warning: {str(payload['errors'])[:120]}"
        )
        return []

    edges = (
        payload
        .get("data", {})
        .get("posts", {})
        .get("edges", [])
    )

    articles = []

    for edge in edges:

        node = edge.get(
            "node",
            {}
        )

        title = node.get(
            "name",
            ""
        )

        if not title:
            continue

        tagline = node.get(
            "tagline",
            ""
        )

        votes = node.get(
            "votesCount",
            0
        )

        comments = node.get(
            "commentsCount",
            0
        )

        articles.append({
            "Title": title,
            "Source": "Product Hunt AI",
            "Published Date": node.get(
                "createdAt",
                ""
            ),
            "URL": node.get(
                "url",
                ""
            ),
            "Summary": (
                f"{tagline} | Product Hunt launch | "
                f"Votes: {votes} | Comments: {comments}"
            ),
            "Category": "",
            "Company Mentioned": "",
            "Keywords": "",
            "Importance Score": 0,
            "Why It Matters": "",
            "SaaS Impact": "",
            "PM Perspective": ""
        })

    return articles
