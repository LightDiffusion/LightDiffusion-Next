import torch.nn as nn
import torch as th

from modules.Utilities import util
from modules.AutoEncoders import ResBlock
from modules.NeuralNetwork import transformer
from modules.cond import cast, cond
from modules.sample import sampling, sampling_util

UNET_MAP_ATTENTIONS = {
    "proj_in.weight",
    "proj_in.bias",
    "proj_out.weight",
    "proj_out.bias",
    "norm.weight",
    "norm.bias",
}

TRANSFORMER_BLOCKS = {
    "norm1.weight",
    "norm1.bias",
    "norm2.weight",
    "norm2.bias",
    "norm3.weight",
    "norm3.bias",
    "attn1.to_q.weight",
    "attn1.to_k.weight",
    "attn1.to_v.weight",
    "attn1.to_out.0.weight",
    "attn1.to_out.0.bias",
    "attn2.to_q.weight",
    "attn2.to_k.weight",
    "attn2.to_v.weight",
    "attn2.to_out.0.weight",
    "attn2.to_out.0.bias",
    "ff.net.0.proj.weight",
    "ff.net.0.proj.bias",
    "ff.net.2.weight",
    "ff.net.2.bias",
}

UNET_MAP_RESNET = {
    "in_layers.2.weight": "conv1.weight",
    "in_layers.2.bias": "conv1.bias",
    "emb_layers.1.weight": "time_emb_proj.weight",
    "emb_layers.1.bias": "time_emb_proj.bias",
    "out_layers.3.weight": "conv2.weight",
    "out_layers.3.bias": "conv2.bias",
    "skip_connection.weight": "conv_shortcut.weight",
    "skip_connection.bias": "conv_shortcut.bias",
    "in_layers.0.weight": "norm1.weight",
    "in_layers.0.bias": "norm1.bias",
    "out_layers.0.weight": "norm2.weight",
    "out_layers.0.bias": "norm2.bias",
}

UNET_MAP_BASIC = {
    ("label_emb.0.0.weight", "class_embedding.linear_1.weight"),
    ("label_emb.0.0.bias", "class_embedding.linear_1.bias"),
    ("label_emb.0.2.weight", "class_embedding.linear_2.weight"),
    ("label_emb.0.2.bias", "class_embedding.linear_2.bias"),
    ("label_emb.0.0.weight", "add_embedding.linear_1.weight"),
    ("label_emb.0.0.bias", "add_embedding.linear_1.bias"),
    ("label_emb.0.2.weight", "add_embedding.linear_2.weight"),
    ("label_emb.0.2.bias", "add_embedding.linear_2.bias"),
    ("input_blocks.0.0.weight", "conv_in.weight"),
    ("input_blocks.0.0.bias", "conv_in.bias"),
    ("out.0.weight", "conv_norm_out.weight"),
    ("out.0.bias", "conv_norm_out.bias"),
    ("out.2.weight", "conv_out.weight"),
    ("out.2.bias", "conv_out.bias"),
    ("time_embed.0.weight", "time_embedding.linear_1.weight"),
    ("time_embed.0.bias", "time_embedding.linear_1.bias"),
    ("time_embed.2.weight", "time_embedding.linear_2.weight"),
    ("time_embed.2.bias", "time_embedding.linear_2.bias"),
}

# taken from https://github.com/TencentARC/T2I-Adapter

def unet_to_diffusers(unet_config):
    """#### Convert a UNet configuration to a diffusers configuration.

    #### Args:
        - `unet_config` (dict): The UNet configuration.

    #### Returns:
        - `dict`: The diffusers configuration.
    """
    if "num_res_blocks" not in unet_config:
        return {}
    num_res_blocks = unet_config["num_res_blocks"]
    channel_mult = unet_config["channel_mult"]
    transformer_depth = unet_config["transformer_depth"][:]
    transformer_depth_output = unet_config["transformer_depth_output"][:]
    num_blocks = len(channel_mult)

    transformers_mid = unet_config.get("transformer_depth_middle", None)

    diffusers_unet_map = {}
    for x in range(num_blocks):
        n = 1 + (num_res_blocks[x] + 1) * x
        for i in range(num_res_blocks[x]):
            for b in UNET_MAP_RESNET:
                diffusers_unet_map[
                    "down_blocks.{}.resnets.{}.{}".format(x, i, UNET_MAP_RESNET[b])
                ] = "input_blocks.{}.0.{}".format(n, b)
            num_transformers = transformer_depth.pop(0)
            if num_transformers > 0:
                for b in UNET_MAP_ATTENTIONS:
                    diffusers_unet_map[
                        "down_blocks.{}.attentions.{}.{}".format(x, i, b)
                    ] = "input_blocks.{}.1.{}".format(n, b)
                for t in range(num_transformers):
                    for b in TRANSFORMER_BLOCKS:
                        diffusers_unet_map[
                            "down_blocks.{}.attentions.{}.transformer_blocks.{}.{}".format(
                                x, i, t, b
                            )
                        ] = "input_blocks.{}.1.transformer_blocks.{}.{}".format(n, t, b)
            n += 1
        for k in ["weight", "bias"]:
            diffusers_unet_map["down_blocks.{}.downsamplers.0.conv.{}".format(x, k)] = (
                "input_blocks.{}.0.op.{}".format(n, k)
            )

    i = 0
    for b in UNET_MAP_ATTENTIONS:
        diffusers_unet_map["mid_block.attentions.{}.{}".format(i, b)] = (
            "middle_block.1.{}".format(b)
        )
    for t in range(transformers_mid):
        for b in TRANSFORMER_BLOCKS:
            diffusers_unet_map[
                "mid_block.attentions.{}.transformer_blocks.{}.{}".format(i, t, b)
            ] = "middle_block.1.transformer_blocks.{}.{}".format(t, b)

    for i, n in enumerate([0, 2]):
        for b in UNET_MAP_RESNET:
            diffusers_unet_map[
                "mid_block.resnets.{}.{}".format(i, UNET_MAP_RESNET[b])
            ] = "middle_block.{}.{}".format(n, b)

    num_res_blocks = list(reversed(num_res_blocks))
    for x in range(num_blocks):
        n = (num_res_blocks[x] + 1) * x
        l = num_res_blocks[x] + 1
        for i in range(l):
            c = 0
            for b in UNET_MAP_RESNET:
                diffusers_unet_map[
                    "up_blocks.{}.resnets.{}.{}".format(x, i, UNET_MAP_RESNET[b])
                ] = "output_blocks.{}.0.{}".format(n, b)
            c += 1
            num_transformers = transformer_depth_output.pop()
            if num_transformers > 0:
                c += 1
                for b in UNET_MAP_ATTENTIONS:
                    diffusers_unet_map[
                        "up_blocks.{}.attentions.{}.{}".format(x, i, b)
                    ] = "output_blocks.{}.1.{}".format(n, b)
                for t in range(num_transformers):
                    for b in TRANSFORMER_BLOCKS:
                        diffusers_unet_map[
                            "up_blocks.{}.attentions.{}.transformer_blocks.{}.{}".format(
                                x, i, t, b
                            )
                        ] = "output_blocks.{}.1.transformer_blocks.{}.{}".format(
                            n, t, b
                        )
            if i == l - 1:
                for k in ["weight", "bias"]:
                    diffusers_unet_map[
                        "up_blocks.{}.upsamplers.0.conv.{}".format(x, k)
                    ] = "output_blocks.{}.{}.conv.{}".format(n, c, k)
            n += 1

    for k in UNET_MAP_BASIC:
        diffusers_unet_map[k[1]] = k[0]

    return diffusers_unet_map

def apply_control1(h, control, name):
    return h

oai_ops = cast.disable_weight_init

class UNetModel1(nn.Module):
    def __init__(
        self,
        image_size,
        in_channels,
        model_channels,
        out_channels,
        num_res_blocks,
        dropout=0,
        channel_mult=(1, 2, 4, 8),
        conv_resample=True,
        dims=2,
        num_classes=None,
        use_checkpoint=False,
        dtype=th.float32,
        num_heads=-1,
        num_head_channels=-1,
        num_heads_upsample=-1,
        use_scale_shift_norm=False,
        resblock_updown=False,
        use_new_attention_order=False,
        use_spatial_transformer=False,  # custom transformer support
        transformer_depth=1,  # custom transformer support
        context_dim=None,  # custom transformer support
        n_embed=None,  # custom support for prediction of discrete ids into codebook of first stage vq model
        legacy=True,
        disable_self_attentions=None,
        num_attention_blocks=None,
        disable_middle_self_attn=False,
        use_linear_in_transformer=False,
        adm_in_channels=None,
        transformer_depth_middle=None,
        transformer_depth_output=None,
        use_temporal_resblock=False,
        use_temporal_attention=False,
        time_context_dim=None,
        extra_ff_mix_layer=False,
        use_spatial_context=False,
        merge_strategy=None,
        merge_factor=0.0,
        video_kernel_size=None,
        disable_temporal_crossattention=False,
        max_ddpm_temb_period=10000,
        device=None,
        operations=oai_ops,
    ):
        super().__init__()

        if context_dim is not None:
            assert (
                use_spatial_transformer
            ), "Fool!! You forgot to use the spatial transformer for your cross-attention conditioning..."
            # from omegaconf.listconfig import ListConfig
            # if type(context_dim) == ListConfig:
            #     context_dim = list(context_dim)

        if num_heads_upsample == -1:
            num_heads_upsample = num_heads
        if num_head_channels == -1:
            assert (
                num_heads != -1
            ), "Either num_heads or num_head_channels has to be set"

        self.in_channels = in_channels
        self.model_channels = model_channels
        self.out_channels = out_channels
        self.num_res_blocks = num_res_blocks

        transformer_depth = transformer_depth[:]
        transformer_depth_output = transformer_depth_output[:]

        self.dropout = dropout
        self.channel_mult = channel_mult
        self.conv_resample = conv_resample
        self.num_classes = num_classes
        self.use_checkpoint = use_checkpoint
        self.dtype = dtype
        self.num_heads = num_heads
        self.num_head_channels = num_head_channels
        self.num_heads_upsample = num_heads_upsample
        self.use_temporal_resblocks = use_temporal_resblock
        self.predict_codebook_ids = n_embed is not None

        self.default_num_video_frames = None

        time_embed_dim = model_channels * 4
        self.time_embed = nn.Sequential(
            operations.Linear(
                model_channels, time_embed_dim, dtype=self.dtype, device=device
            ),
            nn.SiLU(),
            operations.Linear(
                time_embed_dim, time_embed_dim, dtype=self.dtype, device=device
            ),
        )

        self.input_blocks = nn.ModuleList(
            [
                sampling.TimestepEmbedSequential1(
                    operations.conv_nd(
                        dims,
                        in_channels,
                        model_channels,
                        3,
                        padding=1,
                        dtype=self.dtype,
                        device=device,
                    )
                )
            ]
        )
        self._feature_size = model_channels
        input_block_chans = [model_channels]
        ch = model_channels
        ds = 1

        def get_attention_layer(
            ch,
            num_heads,
            dim_head,
            depth=1,
            context_dim=None,
            use_checkpoint=False,
            disable_self_attn=False,
        ):
            return transformer.SpatialTransformer(
                ch,
                num_heads,
                dim_head,
                depth=depth,
                context_dim=context_dim,
                disable_self_attn=disable_self_attn,
                use_linear=use_linear_in_transformer,
                use_checkpoint=use_checkpoint,
                dtype=self.dtype,
                device=device,
                operations=operations,
            )

        def get_resblock(
            merge_factor,
            merge_strategy,
            video_kernel_size,
            ch,
            time_embed_dim,
            dropout,
            out_channels,
            dims,
            use_checkpoint,
            use_scale_shift_norm,
            down=False,
            up=False,
            dtype=None,
            device=None,
            operations=oai_ops,
        ):
            return ResBlock.ResBlock1(
                channels=ch,
                emb_channels=time_embed_dim,
                dropout=dropout,
                out_channels=out_channels,
                use_checkpoint=use_checkpoint,
                dims=dims,
                use_scale_shift_norm=use_scale_shift_norm,
                down=down,
                up=up,
                dtype=dtype,
                device=device,
                operations=operations,
            )

        for level, mult in enumerate(channel_mult):
            for nr in range(self.num_res_blocks[level]):
                layers = [
                    get_resblock(
                        merge_factor=merge_factor,
                        merge_strategy=merge_strategy,
                        video_kernel_size=video_kernel_size,
                        ch=ch,
                        time_embed_dim=time_embed_dim,
                        dropout=dropout,
                        out_channels=mult * model_channels,
                        dims=dims,
                        use_checkpoint=use_checkpoint,
                        use_scale_shift_norm=use_scale_shift_norm,
                        dtype=self.dtype,
                        device=device,
                        operations=operations,
                    )
                ]
                ch = mult * model_channels
                num_transformers = transformer_depth.pop(0)
                if num_transformers > 0:
                    dim_head = ch // num_heads
                    disabled_sa = False

                    if (
                        not util.exists(num_attention_blocks)
                        or nr < num_attention_blocks[level]
                    ):
                        layers.append(
                            get_attention_layer(
                                ch,
                                num_heads,
                                dim_head,
                                depth=num_transformers,
                                context_dim=context_dim,
                                disable_self_attn=disabled_sa,
                                use_checkpoint=use_checkpoint,
                            )
                        )
                self.input_blocks.append(sampling.TimestepEmbedSequential1(*layers))
                self._feature_size += ch
                input_block_chans.append(ch)
            if level != len(channel_mult) - 1:
                out_ch = ch
                self.input_blocks.append(
                    sampling.TimestepEmbedSequential1(
                        get_resblock(
                            merge_factor=merge_factor,
                            merge_strategy=merge_strategy,
                            video_kernel_size=video_kernel_size,
                            ch=ch,
                            time_embed_dim=time_embed_dim,
                            dropout=dropout,
                            out_channels=out_ch,
                            dims=dims,
                            use_checkpoint=use_checkpoint,
                            use_scale_shift_norm=use_scale_shift_norm,
                            down=True,
                            dtype=self.dtype,
                            device=device,
                            operations=operations,
                        )
                        if resblock_updown
                        else ResBlock.Downsample1(
                            ch,
                            conv_resample,
                            dims=dims,
                            out_channels=out_ch,
                            dtype=self.dtype,
                            device=device,
                            operations=operations,
                        )
                    )
                )
                ch = out_ch
                input_block_chans.append(ch)
                ds *= 2
                self._feature_size += ch

        dim_head = ch // num_heads
        mid_block = [
            get_resblock(
                merge_factor=merge_factor,
                merge_strategy=merge_strategy,
                video_kernel_size=video_kernel_size,
                ch=ch,
                time_embed_dim=time_embed_dim,
                dropout=dropout,
                out_channels=None,
                dims=dims,
                use_checkpoint=use_checkpoint,
                use_scale_shift_norm=use_scale_shift_norm,
                dtype=self.dtype,
                device=device,
                operations=operations,
            )
        ]

        self.middle_block = None
        if transformer_depth_middle >= -1:
            if transformer_depth_middle >= 0:
                mid_block += [
                    get_attention_layer(  # always uses a self-attn
                        ch,
                        num_heads,
                        dim_head,
                        depth=transformer_depth_middle,
                        context_dim=context_dim,
                        disable_self_attn=disable_middle_self_attn,
                        use_checkpoint=use_checkpoint,
                    ),
                    get_resblock(
                        merge_factor=merge_factor,
                        merge_strategy=merge_strategy,
                        video_kernel_size=video_kernel_size,
                        ch=ch,
                        time_embed_dim=time_embed_dim,
                        dropout=dropout,
                        out_channels=None,
                        dims=dims,
                        use_checkpoint=use_checkpoint,
                        use_scale_shift_norm=use_scale_shift_norm,
                        dtype=self.dtype,
                        device=device,
                        operations=operations,
                    ),
                ]
            self.middle_block = sampling.TimestepEmbedSequential1(*mid_block)
        self._feature_size += ch

        self.output_blocks = nn.ModuleList([])
        for level, mult in list(enumerate(channel_mult))[::-1]:
            for i in range(self.num_res_blocks[level] + 1):
                ich = input_block_chans.pop()
                layers = [
                    get_resblock(
                        merge_factor=merge_factor,
                        merge_strategy=merge_strategy,
                        video_kernel_size=video_kernel_size,
                        ch=ch + ich,
                        time_embed_dim=time_embed_dim,
                        dropout=dropout,
                        out_channels=model_channels * mult,
                        dims=dims,
                        use_checkpoint=use_checkpoint,
                        use_scale_shift_norm=use_scale_shift_norm,
                        dtype=self.dtype,
                        device=device,
                        operations=operations,
                    )
                ]
                ch = model_channels * mult
                num_transformers = transformer_depth_output.pop()
                if num_transformers > 0:
                    dim_head = ch // num_heads
                    disabled_sa = False

                    if (
                        not util.exists(num_attention_blocks)
                        or i < num_attention_blocks[level]
                    ):
                        layers.append(
                            get_attention_layer(
                                ch,
                                num_heads,
                                dim_head,
                                depth=num_transformers,
                                context_dim=context_dim,
                                disable_self_attn=disabled_sa,
                                use_checkpoint=use_checkpoint,
                            )
                        )
                if level and i == self.num_res_blocks[level]:
                    out_ch = ch
                    layers.append(
                        get_resblock(
                            merge_factor=merge_factor,
                            merge_strategy=merge_strategy,
                            video_kernel_size=video_kernel_size,
                            ch=ch,
                            time_embed_dim=time_embed_dim,
                            dropout=dropout,
                            out_channels=out_ch,
                            dims=dims,
                            use_checkpoint=use_checkpoint,
                            use_scale_shift_norm=use_scale_shift_norm,
                            up=True,
                            dtype=self.dtype,
                            device=device,
                            operations=operations,
                        )
                        if resblock_updown
                        else ResBlock.Upsample1(
                            ch,
                            conv_resample,
                            dims=dims,
                            out_channels=out_ch,
                            dtype=self.dtype,
                            device=device,
                            operations=operations,
                        )
                    )
                    ds //= 2
                self.output_blocks.append(sampling.TimestepEmbedSequential1(*layers))
                self._feature_size += ch

        self.out = nn.Sequential(
            operations.GroupNorm(32, ch, dtype=self.dtype, device=device),
            nn.SiLU(),
            util.zero_module(
                operations.conv_nd(
                    dims,
                    model_channels,
                    out_channels,
                    3,
                    padding=1,
                    dtype=self.dtype,
                    device=device,
                )
            ),
        )

    def forward(
        self,
        x,
        timesteps=None,
        context=None,
        y=None,
        control=None,
        transformer_options={},
        **kwargs,
    ):
        transformer_options["original_shape"] = list(x.shape)
        transformer_options["transformer_index"] = 0
        transformer_patches = transformer_options.get("patches", {})

        num_video_frames = kwargs.get("num_video_frames", self.default_num_video_frames)
        image_only_indicator = kwargs.get("image_only_indicator", None)
        time_context = kwargs.get("time_context", None)

        assert (y is not None) == (
            self.num_classes is not None
        ), "must specify y if and only if the model is class-conditional"
        hs = []
        t_emb = sampling_util.timestep_embedding(
            timesteps, self.model_channels, repeat_only=False
        ).to(x.dtype)
        emb = self.time_embed(t_emb)
        h = x
        for id, module in enumerate(self.input_blocks):
            transformer_options["block"] = ("input", id)
            h = ResBlock.forward_timestep_embed1(
                module,
                h,
                emb,
                context,
                transformer_options,
                time_context=time_context,
                num_video_frames=num_video_frames,
                image_only_indicator=image_only_indicator,
            )
            h = apply_control1(h, control, "input")
            hs.append(h)

        transformer_options["block"] = ("middle", 0)
        if self.middle_block is not None:
            h = ResBlock.forward_timestep_embed1(
                self.middle_block,
                h,
                emb,
                context,
                transformer_options,
                time_context=time_context,
                num_video_frames=num_video_frames,
                image_only_indicator=image_only_indicator,
            )
        h = apply_control1(h, control, "middle")

        for id, module in enumerate(self.output_blocks):
            transformer_options["block"] = ("output", id)
            hsp = hs.pop()
            hsp = apply_control1(hsp, control, "output")

            h = th.cat([h, hsp], dim=1)
            del hsp
            if len(hs) > 0:
                output_shape = hs[-1].shape
            else:
                output_shape = None
            h = ResBlock.forward_timestep_embed1(
                module,
                h,
                emb,
                context,
                transformer_options,
                output_shape,
                time_context=time_context,
                num_video_frames=num_video_frames,
                image_only_indicator=image_only_indicator,
            )
        h = h.type(x.dtype)
        return self.out(h)

def detect_unet_config(state_dict, key_prefix):
    state_dict_keys = list(state_dict.keys())

    unet_config = {
        "use_checkpoint": False,
        "image_size": 32,
        "use_spatial_transformer": True,
        "legacy": False,
    }

    y_input = "{}label_emb.0.0.weight".format(key_prefix)
    unet_config["adm_in_channels"] = None

    model_channels = state_dict["{}input_blocks.0.0.weight".format(key_prefix)].shape[0]
    in_channels = state_dict["{}input_blocks.0.0.weight".format(key_prefix)].shape[1]

    out_key = "{}out.2.weight".format(key_prefix)
    out_channels = state_dict[out_key].shape[0]

    num_res_blocks = []
    channel_mult = []
    attention_resolutions = []
    transformer_depth = []
    transformer_depth_output = []
    context_dim = None
    use_linear_in_transformer = False

    video_model = False

    current_res = 1
    count = 0

    last_res_blocks = 0
    last_channel_mult = 0

    input_block_count = transformer.count_blocks(
        state_dict_keys, "{}input_blocks".format(key_prefix) + ".{}."
    )
    for count in range(input_block_count):
        prefix = "{}input_blocks.{}.".format(key_prefix, count)
        prefix_output = "{}output_blocks.{}.".format(
            key_prefix, input_block_count - count - 1
        )

        block_keys = sorted(
            list(filter(lambda a: a.startswith(prefix), state_dict_keys))
        )

        block_keys_output = sorted(
            list(filter(lambda a: a.startswith(prefix_output), state_dict_keys))
        )

        if "{}0.op.weight".format(prefix) in block_keys:  # new layer
            num_res_blocks.append(last_res_blocks)
            channel_mult.append(last_channel_mult)

            current_res *= 2
            last_res_blocks = 0
            last_channel_mult = 0
            out = transformer.calculate_transformer_depth(
                prefix_output, state_dict_keys, state_dict
            )
            if out is not None:
                transformer_depth_output.append(out[0])
            else:
                transformer_depth_output.append(0)
        else:
            res_block_prefix = "{}0.in_layers.0.weight".format(prefix)
            if res_block_prefix in block_keys:
                last_res_blocks += 1
                last_channel_mult = (
                    state_dict["{}0.out_layers.3.weight".format(prefix)].shape[0]
                    // model_channels
                )

                out = transformer.calculate_transformer_depth(prefix, state_dict_keys, state_dict)
                if out is not None:
                    transformer_depth.append(out[0])
                    if context_dim is None:
                        context_dim = out[1]
                        use_linear_in_transformer = out[2]
                        video_model = out[3]
                else:
                    transformer_depth.append(0)

            res_block_prefix = "{}0.in_layers.0.weight".format(prefix_output)
            if res_block_prefix in block_keys_output:
                out = transformer.calculate_transformer_depth(
                    prefix_output, state_dict_keys, state_dict
                )
                if out is not None:
                    transformer_depth_output.append(out[0])
                else:
                    transformer_depth_output.append(0)

    num_res_blocks.append(last_res_blocks)
    channel_mult.append(last_channel_mult)
    if "{}middle_block.1.proj_in.weight".format(key_prefix) in state_dict_keys:
        transformer_depth_middle = transformer.count_blocks(
            state_dict_keys,
            "{}middle_block.1.transformer_blocks.".format(key_prefix) + "{}",
        )

    unet_config["in_channels"] = in_channels
    unet_config["out_channels"] = out_channels
    unet_config["model_channels"] = model_channels
    unet_config["num_res_blocks"] = num_res_blocks
    unet_config["transformer_depth"] = transformer_depth
    unet_config["transformer_depth_output"] = transformer_depth_output
    unet_config["channel_mult"] = channel_mult
    unet_config["transformer_depth_middle"] = transformer_depth_middle
    unet_config["use_linear_in_transformer"] = use_linear_in_transformer
    unet_config["context_dim"] = context_dim

    unet_config["use_temporal_resblock"] = False
    unet_config["use_temporal_attention"] = False

    return unet_config


def model_config_from_unet_config(unet_config, state_dict=None):
    from modules.SD15 import SD15
    for model_config in SD15.models:
        if model_config.matches(unet_config, state_dict):
            return model_config(unet_config)


def model_config_from_unet(state_dict, unet_key_prefix, use_base_if_no_match=False):
    unet_config = detect_unet_config(state_dict, unet_key_prefix)
    model_config = model_config_from_unet_config(unet_config, state_dict)
    return model_config

def unet_dtype1(
    device=None,
    model_params=0,
    supported_dtypes=[th.float16, th.bfloat16, th.float32],
):
    return th.float16