let meta = #{
    name: "sync-youth",
    description: "온통청년 정책 전체 목록을 받아 스냅샷을 갱신하고 저장소에 올린다",
    when_to_use: "온통청년 캐시를 다시 받을 때, 또는 배포 목록이 오래됐을 때",
    phases: [
        #{ title: "Refresh", detail: "getPlcy 전체 페이지를 받아 스냅샷 저장" },
        #{ title: "Publish", detail: "변경이 있으면 commit 후 push" },
    ],
};

let refresh_schema = #{
    "type": "object",
    "required": ["ok", "count", "path"],
    "properties": #{
        "ok": #{ "type": "boolean" },
        "count": #{ "type": "integer" },
        "tot_count": #{ "type": "integer" },
        "path": #{ "type": "string" },
        "reason": #{ "type": "string" },
    },
};
let publish_schema = #{
    "type": "object",
    "required": ["ok", "published"],
    "properties": #{
        "ok": #{ "type": "boolean" },
        "published": #{ "type": "boolean" },
        "reason": #{ "type": "string" },
    },
};

let want_publish = true;
if args != () && args.commit == false { want_publish = false; }

phase("Refresh");
let refresh_prompt = "Work only in the CODYSSEY_6_ProJect repo (C:\\Users\\seong\\Downloads\\CODYSSEY_6_ProJect).";
refresh_prompt += " Run: py -3 scripts/sync_youth.py";
refresh_prompt += " That script walks 온통청년 getPlcy pageSize=100 until the last page and writes data/youth_policy_snapshot.json.";
refresh_prompt += " Do not print .env or API keys. Do not edit other/.";
refresh_prompt += " After it finishes, read the last lines of output and confirm the file exists.";
refresh_prompt += " Return {ok, count, tot_count, path, reason}. ok=true only if count is at least 1000.";

let refresh_run = agent(refresh_prompt, #{
    label: "refresh-snapshot",
    capability_mode: "execute",
    output_schema: refresh_schema,
});

if refresh_run == () || !refresh_run.success || refresh_run.output == () {
    complete(#{ ok: false, reason: "refresh agent failed" });
}

let item_count = 0;
if refresh_run.output.count != () { item_count = refresh_run.output.count; }
if item_count != 0 && item_count < 1000 {
    complete(#{ ok: false, reason: "snapshot too small", count: item_count });
}
if refresh_run.output.ok == false {
    complete(#{ ok: false, reason: "refresh reported not ok", count: item_count });
}

if !want_publish {
    complete(#{ ok: true, published: false, count: item_count, path: refresh_run.output.path });
}

phase("Publish");
let publish_prompt = "Work only in the CODYSSEY_6_ProJect repo.";
publish_prompt += " Stage only data/youth_policy_snapshot.json.";
publish_prompt += " If that file has no staged diff, do not commit. Return {ok:true, published:false, reason:\"no change\"}.";
publish_prompt += " If it changed, commit with message 'chore: 온통청년 정책 스냅샷 갱신' and git push origin main.";
publish_prompt += " Never add .env, other/, or API keys. Return {ok, published, reason}.";

let publish_run = agent(publish_prompt, #{
    label: "publish-snapshot",
    capability_mode: "execute",
    output_schema: publish_schema,
});

if publish_run == () || !publish_run.success || publish_run.output == () {
    complete(#{ ok: false, reason: "publish agent failed", count: item_count });
}

complete(#{
    ok: publish_run.output.ok,
    published: publish_run.output.published,
    count: item_count,
    path: refresh_run.output.path,
    reason: publish_run.output.reason,
});
