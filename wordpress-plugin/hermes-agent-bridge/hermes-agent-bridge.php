<?php
/**
 * Plugin Name: Hermes Agent Bridge
 * Description: Minimal REST bridge for Hermes Agent WordPress automation.
 * Version: 0.1.0
 * Author: Hermes LINE WordPress Agent contributors
 * License: MIT
 */

if (!defined('ABSPATH')) {
    exit;
}

function hermes_agent_bridge_expected_token() {
    if (defined('HERMES_AGENT_BRIDGE_TOKEN')) {
        return HERMES_AGENT_BRIDGE_TOKEN;
    }

    $env = getenv('HERMES_AGENT_BRIDGE_TOKEN');
    return is_string($env) ? $env : '';
}

function hermes_agent_bridge_check_token(WP_REST_Request $request) {
    $expected = hermes_agent_bridge_expected_token();
    if ($expected === '') {
        return new WP_Error('hermes_bridge_not_configured', 'Bridge token is not configured.', array('status' => 403));
    }

    $provided = $request->get_header('x-hermes-bridge-token');
    if (!hash_equals($expected, (string) $provided)) {
        return new WP_Error('hermes_bridge_forbidden', 'Invalid bridge token.', array('status' => 403));
    }

    return true;
}

function hermes_agent_bridge_can_edit_post(WP_REST_Request $request) {
    $token_check = hermes_agent_bridge_check_token($request);
    if (is_wp_error($token_check)) {
        return $token_check;
    }

    $post_id = absint($request['post_id']);
    if (!$post_id || !current_user_can('edit_post', $post_id)) {
        return new WP_Error('hermes_bridge_cannot_edit', 'Current user cannot edit this post.', array('status' => 403));
    }

    return true;
}

function hermes_agent_bridge_update_seo_meta(WP_REST_Request $request) {
    $post_id = absint($request['post_id']);
    $plugin = sanitize_text_field($request->get_param('plugin') ?: 'auto');
    $title = $request->get_param('title');
    $description = $request->get_param('description');
    $focus_keyword = $request->get_param('focus_keyword');
    $updated = array();

    if ($title !== null) {
        $value = sanitize_text_field($title);
        update_post_meta($post_id, '_yoast_wpseo_title', $value);
        update_post_meta($post_id, 'rank_math_title', $value);
        $updated[] = 'title';
    }

    if ($description !== null) {
        $value = sanitize_textarea_field($description);
        update_post_meta($post_id, '_yoast_wpseo_metadesc', $value);
        update_post_meta($post_id, 'rank_math_description', $value);
        $updated[] = 'description';
    }

    if ($focus_keyword !== null) {
        $value = sanitize_text_field($focus_keyword);
        update_post_meta($post_id, '_yoast_wpseo_focuskw', $value);
        update_post_meta($post_id, 'rank_math_focus_keyword', $value);
        $updated[] = 'focus_keyword';
    }

    return rest_ensure_response(array(
        'ok' => true,
        'post_id' => $post_id,
        'plugin' => $plugin,
        'updated' => $updated,
    ));
}

add_action('rest_api_init', function () {
    register_rest_route('hermes-agent/v1', '/health', array(
        'methods' => 'GET',
        'callback' => function () {
            return rest_ensure_response(array(
                'ok' => true,
                'plugin' => 'hermes-agent-bridge',
                'version' => '0.1.0',
            ));
        },
        'permission_callback' => 'hermes_agent_bridge_check_token',
    ));

    register_rest_route('hermes-agent/v1', '/seo-meta/(?P<post_id>\d+)', array(
        'methods' => 'POST',
        'callback' => 'hermes_agent_bridge_update_seo_meta',
        'permission_callback' => 'hermes_agent_bridge_can_edit_post',
        'args' => array(
            'post_id' => array(
                'required' => true,
                'validate_callback' => function ($value) {
                    return absint($value) > 0;
                },
            ),
        ),
    ));
});

